# Exercise + Diet Starter Plan & Tracker (CLI)

A simple Python CLI to help you start an exercise plan and track diet. It stores data locally in a SQLite database (`fitness.db`).

## Quickstart

```bash
python3 fitness.py init --name "Your Name"
python3 fitness.py today
```

## Common commands

- Initialize starter plan and defaults
  ```bash
  python3 fitness.py init --name "Your Name"
  ```

- Log a workout
  ```bash
  python3 fitness.py add-workout --type strength --duration 45 --notes "Workout A"
  ```

- Log a meal (calories auto-computed if macros given and calories omitted)
  ```bash
  python3 fitness.py add-meal --meal-type lunch --calories 650 --protein 40 --carbs 70 --fat 20 --items "Chicken rice bowl"
  ```

- Set goals
  ```bash
  python3 fitness.py set-goal daily_calories 1800 --unit kcal
  python3 fitness.py set-goal daily_protein_g 120 --unit g
  python3 fitness.py set-goal weekly_exercise_minutes 150 --unit min
  python3 fitness.py set-goal daily_walk_minutes 30 --unit min
  ```

- See today's checklist and progress
  ```bash
  python3 fitness.py today
  ```

- See current week summary
  ```bash
  python3 fitness.py week
  ```

- Show the seeded 4-week starter plan
  ```bash
  python3 fitness.py plan
  ```

- Export data to CSV
  ```bash
  python3 fitness.py export meals > meals.csv
  python3 fitness.py export workouts > workouts.csv
  ```

## Notes

- Database lives beside the script: `fitness.db`.
- Dates default to today; provide `--date YYYY-MM-DD` to backfill entries.
- This is dependency-free (Python standard library only). Ensure Python 3.8+ is available.