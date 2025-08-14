#!/usr/bin/env python3

import argparse
import os
import sqlite3
import sys
from datetime import datetime, date, timedelta
from typing import Optional, Tuple, Dict, Any, List


# ------------------------------
# Database helpers
# ------------------------------

DB_FILENAME = "fitness.db"


def get_db_path() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_FILENAME)


def get_db_connection() -> sqlite3.Connection:
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_db_schema(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS profile (
            id INTEGER PRIMARY KEY CHECK (id=1),
            name TEXT,
            start_date TEXT
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY,
            key TEXT UNIQUE NOT NULL,
            value REAL NOT NULL,
            unit TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY,
            date TEXT NOT NULL,
            type TEXT NOT NULL,
            duration_min REAL,
            distance_km REAL,
            sets INTEGER,
            reps INTEGER,
            weight_kg REAL,
            notes TEXT,
            created_at TEXT NOT NULL
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY,
            date TEXT NOT NULL,
            meal_type TEXT NOT NULL,
            calories REAL,
            protein_g REAL,
            carbs_g REAL,
            fat_g REAL,
            items TEXT,
            created_at TEXT NOT NULL
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS plan_workouts (
            id INTEGER PRIMARY KEY,
            week INTEGER NOT NULL,
            dow INTEGER NOT NULL, -- Monday=1 ... Sunday=7
            name TEXT NOT NULL,
            details TEXT NOT NULL
        );
        """
    )

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_workouts_date ON workouts(date);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_meals_date ON meals(date);")
    conn.commit()


# ------------------------------
# Utilities
# ------------------------------


def iso_today() -> str:
    return date.today().isoformat()


def iso_week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


def parse_date(value: Optional[str]) -> str:
    if not value:
        return iso_today()
    try:
        # Accept YYYY-MM-DD
        return datetime.strptime(value, "%Y-%m-%d").date().isoformat()
    except ValueError:
        print("Invalid date format. Use YYYY-MM-DD.", file=sys.stderr)
        sys.exit(1)


def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def get_week_number_since(start_date: date, target_date: date) -> int:
    delta_days = (iso_week_start(target_date) - iso_week_start(start_date)).days
    return delta_days // 7 + 1


def print_progress(label: str, current: float, goal: float, unit: str, width: int = 24) -> None:
    current = max(0.0, current)
    goal = max(0.0, goal)
    ratio = 0.0 if goal == 0 else min(1.0, current / goal)
    filled = int(ratio * width)
    bar = "#" * filled + "-" * (width - filled)
    print(f"{label:20} [{bar}] {current:.0f}/{goal:.0f} {unit}")


# ------------------------------
# Seed plan and default goals
# ------------------------------

DEFAULT_PLAN = [
    # 4-week beginner plan. Strength 3x/week, easy cardio, daily walks
    # Week 1-4 share the same pattern for simplicity
    # Monday (1): Workout A
    (1, 1, "Workout A", "Full-body: Squat 3x8, Push-up 3xAMRAP, Row 3x10, Plank 3x30s"),
    (2, 1, "Workout A", "Full-body: Squat 3x8, Push-up 3xAMRAP, Row 3x10, Plank 3x30s"),
    (3, 1, "Workout A", "Full-body: Squat 3x8, Push-up 3xAMRAP, Row 3x10, Plank 3x30s"),
    (4, 1, "Workout A", "Full-body: Squat 3x8, Push-up 3xAMRAP, Row 3x10, Plank 3x30s"),
    # Wednesday (3): Workout B
    (1, 3, "Workout B", "Full-body: Hinge 3x8, Overhead Press 3x8, Lat Pull 3x10, Side Plank 3x30s"),
    (2, 3, "Workout B", "Full-body: Hinge 3x8, Overhead Press 3x8, Lat Pull 3x10, Side Plank 3x30s"),
    (3, 3, "Workout B", "Full-body: Hinge 3x8, Overhead Press 3x8, Lat Pull 3x10, Side Plank 3x30s"),
    (4, 3, "Workout B", "Full-body: Hinge 3x8, Overhead Press 3x8, Lat Pull 3x10, Side Plank 3x30s"),
    # Friday (5): Workout C
    (1, 5, "Workout C", "Full-body: Lunge 3x8/leg, Bench 3x8, Row 3x10, Deadbug 3x10/side"),
    (2, 5, "Workout C", "Full-body: Lunge 3x8/leg, Bench 3x8, Row 3x10, Deadbug 3x10/side"),
    (3, 5, "Workout C", "Full-body: Lunge 3x8/leg, Bench 3x8, Row 3x10, Deadbug 3x10/side"),
    (4, 5, "Workout C", "Full-body: Lunge 3x8/leg, Bench 3x8, Row 3x10, Deadbug 3x10/side"),
]

DEFAULT_GOALS = [
    ("daily_calories", 1800, "kcal"),
    ("daily_protein_g", 120, "g"),
    ("weekly_exercise_minutes", 150, "min"),
    ("daily_walk_minutes", 30, "min"),
]


def seed_defaults(conn: sqlite3.Connection, name: Optional[str]) -> None:
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM profile WHERE id=1;")
    exists = cursor.fetchone() is not None
    if not exists:
        cursor.execute(
            "INSERT INTO profile (id, name, start_date) VALUES (1, ?, ?);",
            (name or "You", iso_today()),
        )

    cursor.execute("SELECT COUNT(*) AS c FROM plan_workouts;")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO plan_workouts (week, dow, name, details) VALUES (?, ?, ?, ?);",
            DEFAULT_PLAN,
        )

    for key, value, unit in DEFAULT_GOALS:
        cursor.execute(
            "INSERT OR IGNORE INTO goals (key, value, unit, updated_at) VALUES (?, ?, ?, ?);",
            (key, value, unit, now_iso()),
        )

    conn.commit()


# ------------------------------
# Core operations
# ------------------------------


def set_goal(conn: sqlite3.Connection, key: str, value: float, unit: Optional[str]) -> None:
    cursor = conn.cursor()
    if unit is None:
        cursor.execute("SELECT unit FROM goals WHERE key=?;", (key,))
        row = cursor.fetchone()
        unit = row[0] if row else ""
    cursor.execute(
        "INSERT INTO goals (key, value, unit, updated_at) VALUES (?, ?, ?, ?)\n         ON CONFLICT(key) DO UPDATE SET value=excluded.value, unit=excluded.unit, updated_at=excluded.updated_at;",
        (key, float(value), unit, now_iso()),
    )
    conn.commit()


def add_workout(
    conn: sqlite3.Connection,
    date_str: str,
    workout_type: str,
    duration_min: Optional[float],
    distance_km: Optional[float],
    sets: Optional[int],
    reps: Optional[int],
    weight_kg: Optional[float],
    notes: Optional[str],
) -> None:
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO workouts (date, type, duration_min, distance_km, sets, reps, weight_kg, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (
            date_str,
            workout_type,
            duration_min,
            distance_km,
            sets,
            reps,
            weight_kg,
            notes,
            now_iso(),
        ),
    )
    conn.commit()


def add_meal(
    conn: sqlite3.Connection,
    date_str: str,
    meal_type: str,
    calories: Optional[float],
    protein_g: Optional[float],
    carbs_g: Optional[float],
    fat_g: Optional[float],
    items: Optional[str],
) -> None:
    # If calories missing but macros provided, compute estimate
    if calories is None and None not in (protein_g, carbs_g, fat_g):
        calories = 4.0 * float(protein_g) + 4.0 * float(carbs_g) + 9.0 * float(fat_g)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO meals (date, meal_type, calories, protein_g, carbs_g, fat_g, items, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (
            date_str,
            meal_type,
            calories,
            protein_g,
            carbs_g,
            fat_g,
            items,
            now_iso(),
        ),
    )
    conn.commit()


def get_goal(conn: sqlite3.Connection, key: str) -> Tuple[float, str]:
    cursor = conn.cursor()
    cursor.execute("SELECT value, unit FROM goals WHERE key=?;", (key,))
    row = cursor.fetchone()
    if not row:
        return (0.0, "")
    return (float(row[0]), str(row[1]))


def get_profile(conn: sqlite3.Connection) -> Dict[str, Any]:
    cursor = conn.cursor()
    cursor.execute("SELECT name, start_date FROM profile WHERE id=1;")
    row = cursor.fetchone()
    if not row:
        return {"name": "You", "start_date": iso_today()}
    return {"name": row[0], "start_date": row[1]}


def sum_today(conn: sqlite3.Connection, today_str: str) -> Dict[str, float]:
    cursor = conn.cursor()

    cursor.execute("SELECT COALESCE(SUM(calories), 0) FROM meals WHERE date=?;", (today_str,))
    calories = float(cursor.fetchone()[0])

    cursor.execute("SELECT COALESCE(SUM(protein_g), 0) FROM meals WHERE date=?;", (today_str,))
    protein = float(cursor.fetchone()[0])

    cursor.execute("SELECT COALESCE(SUM(duration_min), 0) FROM workouts WHERE date=?;", (today_str,))
    exercise_min = float(cursor.fetchone()[0])

    cursor.execute("SELECT COALESCE(SUM(duration_min), 0) FROM workouts WHERE date BETWEEN ? AND ?;", (
        iso_week_start(date.fromisoformat(today_str)).isoformat(),
        (iso_week_start(date.fromisoformat(today_str)) + timedelta(days=6)).isoformat(),
    ))
    week_exercise_min = float(cursor.fetchone()[0])

    return {
        "calories": calories,
        "protein": protein,
        "exercise_min": exercise_min,
        "week_exercise_min": week_exercise_min,
    }


def get_today_plan(conn: sqlite3.Connection, today_date: date) -> Optional[Dict[str, str]]:
    profile = get_profile(conn)
    start = date.fromisoformat(profile["start_date"]) if profile.get("start_date") else today_date
    week_number = get_week_number_since(start, today_date)
    week_number = max(1, min(4, week_number))  # Cap to 4-week seed plan
    dow = today_date.isoweekday()

    cursor = conn.cursor()
    cursor.execute(
        "SELECT name, details FROM plan_workouts WHERE week=? AND dow=?;",
        (week_number, dow),
    )
    row = cursor.fetchone()
    if not row:
        return None
    return {"name": str(row[0]), "details": str(row[1])}


# ------------------------------
# CLI commands
# ------------------------------


def cmd_init(args: argparse.Namespace) -> None:
    conn = get_db_connection()
    ensure_db_schema(conn)
    seed_defaults(conn, args.name)
    profile = get_profile(conn)
    print(f"Initialized plan for {profile['name']} starting {profile['start_date']}. DB: {get_db_path()}")


def cmd_set_goal(args: argparse.Namespace) -> None:
    conn = get_db_connection()
    ensure_db_schema(conn)
    set_goal(conn, args.key, float(args.value), args.unit)
    value, unit = get_goal(conn, args.key)
    print(f"Set goal {args.key} = {value} {unit}")


def cmd_add_workout(args: argparse.Namespace) -> None:
    conn = get_db_connection()
    ensure_db_schema(conn)
    add_workout(
        conn,
        parse_date(args.date),
        args.type,
        float(args.duration) if args.duration is not None else None,
        float(args.distance) if args.distance is not None else None,
        int(args.sets) if args.sets is not None else None,
        int(args.reps) if args.reps is not None else None,
        float(args.weight) if args.weight is not None else None,
        args.notes,
    )
    print("Workout logged.")


def cmd_add_meal(args: argparse.Namespace) -> None:
    conn = get_db_connection()
    ensure_db_schema(conn)
    add_meal(
        conn,
        parse_date(args.date),
        args.meal_type,
        float(args.calories) if args.calories is not None else None,
        float(args.protein) if args.protein is not None else None,
        float(args.carbs) if args.carbs is not None else None,
        float(args.fat) if args.fat is not None else None,
        args.items,
    )
    print("Meal logged.")


def cmd_today(args: argparse.Namespace) -> None:
    conn = get_db_connection()
    ensure_db_schema(conn)
    today_dt = date.today()
    today_str = today_dt.isoformat()

    profile = get_profile(conn)
    print(f"Today: {today_str} | Plan owner: {profile['name']}")

    plan = get_today_plan(conn, today_dt)
    if plan:
        print(f"Suggested workout: {plan['name']} - {plan['details']}")
    else:
        print("No specific workout planned today. Consider a 20-30 min walk.")

    totals = sum_today(conn, today_str)

    cal_goal, cal_unit = get_goal(conn, "daily_calories")
    prot_goal, prot_unit = get_goal(conn, "daily_protein_g")
    walk_goal, walk_unit = get_goal(conn, "daily_walk_minutes")
    week_ex_goal, week_ex_unit = get_goal(conn, "weekly_exercise_minutes")

    print("")
    print("Nutrition")
    print_progress("Calories", totals["calories"], cal_goal, cal_unit)
    print_progress("Protein", totals["protein"], prot_goal, prot_unit)

    print("")
    print("Exercise")
    print_progress("Today's minutes", totals["exercise_min"], walk_goal, walk_unit)
    print_progress("This week", totals["week_exercise_min"], week_ex_goal, week_ex_unit)


def cmd_week(args: argparse.Namespace) -> None:
    conn = get_db_connection()
    ensure_db_schema(conn)

    today_dt = date.today()
    start = iso_week_start(today_dt)
    end = start + timedelta(days=6)

    cursor = conn.cursor()

    cursor.execute(
        "SELECT COALESCE(SUM(duration_min), 0) FROM workouts WHERE date BETWEEN ? AND ?;",
        (start.isoformat(), end.isoformat()),
    )
    week_minutes = float(cursor.fetchone()[0])

    cursor.execute(
        "SELECT COALESCE(SUM(calories), 0), COALESCE(SUM(protein_g), 0) FROM meals WHERE date BETWEEN ? AND ?;",
        (start.isoformat(), end.isoformat()),
    )
    row = cursor.fetchone()
    week_calories = float(row[0])
    week_protein = float(row[1])

    week_ex_goal, week_ex_unit = get_goal(conn, "weekly_exercise_minutes")

    print(f"Week: {start.isoformat()} to {end.isoformat()}")
    print_progress("Exercise minutes", week_minutes, week_ex_goal, week_ex_unit)
    print(f"Total calories: {week_calories:.0f} kcal | Total protein: {week_protein:.0f} g")


def cmd_plan(args: argparse.Namespace) -> None:
    conn = get_db_connection()
    ensure_db_schema(conn)

    cursor = conn.cursor()
    cursor.execute("SELECT week, dow, name, details FROM plan_workouts ORDER BY week, dow;")
    rows = cursor.fetchall()

    if not rows:
        print("No plan found. Run `init` to create a starter plan.")
        return

    print("4-week starter plan")
    dow_map = {1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat", 7: "Sun"}
    for r in rows:
        week, dow, name, details = r
        print(f"Week {week} {dow_map.get(dow, '?')}: {name} — {details}")


def cmd_export(args: argparse.Namespace) -> None:
    conn = get_db_connection()
    ensure_db_schema(conn)

    table = args.table
    valid = {"workouts", "meals", "goals"}
    if table not in valid:
        print("Invalid table. Choose from: workouts, meals, goals", file=sys.stderr)
        sys.exit(1)

    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table} ORDER BY id;")
    rows = cursor.fetchall()
    cols = [d[0] for d in cursor.description]

    print(",".join(cols))
    for row in rows:
        values = []
        for c in cols:
            v = row[c]
            if v is None:
                values.append("")
            else:
                s = str(v)
                if "," in s or "\n" in s or '"' in s:
                    s = '"' + s.replace('"', '""') + '"'
                values.append(s)
        print(",".join(values))


# ------------------------------
# Parser setup
# ------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Exercise + Diet Starter Plan & Tracker",
    )
    sub = parser.add_subparsers(dest="command")

    p_init = sub.add_parser("init", help="Initialize the database and a 4-week starter plan")
    p_init.add_argument("--name", help="Your name to personalize the plan")
    p_init.set_defaults(func=cmd_init)

    p_goal = sub.add_parser("set-goal", help="Set a goal, e.g., daily_calories or weekly_exercise_minutes")
    p_goal.add_argument("key", help="Goal key, e.g., daily_calories, daily_protein_g, weekly_exercise_minutes, daily_walk_minutes")
    p_goal.add_argument("value", type=float, help="Goal value")
    p_goal.add_argument("--unit", help="Unit (defaults to existing or empty)")
    p_goal.set_defaults(func=cmd_set_goal)

    p_w = sub.add_parser("add-workout", help="Log a workout")
    p_w.add_argument("--date", help="YYYY-MM-DD (default: today)")
    p_w.add_argument("--type", default="strength", help="Type: strength, run, walk, cycle, yoga, etc.")
    p_w.add_argument("--duration", type=float, help="Minutes")
    p_w.add_argument("--distance", type=float, help="Kilometers")
    p_w.add_argument("--sets", type=int, help="Sets")
    p_w.add_argument("--reps", type=int, help="Reps")
    p_w.add_argument("--weight", type=float, help="Weight in kg")
    p_w.add_argument("--notes", help="Freeform notes")
    p_w.set_defaults(func=cmd_add_workout)

    p_m = sub.add_parser("add-meal", help="Log a meal/snack")
    p_m.add_argument("--date", help="YYYY-MM-DD (default: today)")
    p_m.add_argument("--meal-type", dest="meal_type", default="meal", help="breakfast, lunch, dinner, snack")
    p_m.add_argument("--calories", type=float, help="Calories (kcal)")
    p_m.add_argument("--protein", type=float, help="Protein (g)")
    p_m.add_argument("--carbs", type=float, help="Carbs (g)")
    p_m.add_argument("--fat", type=float, help="Fat (g)")
    p_m.add_argument("--items", help="Describe food items")
    p_m.set_defaults(func=cmd_add_meal)

    p_today = sub.add_parser("today", help="Show today's plan and progress")
    p_today.set_defaults(func=cmd_today)

    p_week = sub.add_parser("week", help="Show this week's summary")
    p_week.set_defaults(func=cmd_week)

    p_plan = sub.add_parser("plan", help="Show the 4-week starter plan")
    p_plan.set_defaults(func=cmd_plan)

    p_export = sub.add_parser("export", help="Export a table as CSV to stdout")
    p_export.add_argument("table", help="workouts | meals | goals")
    p_export.set_defaults(func=cmd_export)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0
    try:
        args.func(args)
        return 0
    except sqlite3.Error as e:
        print(f"Database error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())