# Tower of Hanoi (Web)

A modern, accessible, single‑file implementation of the Tower of Hanoi puzzle with drag‑and‑drop, click‑to‑move, keyboard support, and an animated auto‑solver. All logic, styles, and markup live in `twitter.html`.

### Quick start
- Open `twitter.html` in any modern browser (Chrome, Firefox, Edge, Safari).
- No build tools or server required.

### How to play
- Move the entire stack from the Source peg to the Destination peg.
- Only one disk can be moved at a time.
- A larger disk may never be placed on a smaller disk.

### Controls
- **Number of Disks**: Set a value between 3 and 10, then it resets automatically.
- **Reset**: Restarts the game with the current disk count.
- **Auto Solve**: Runs the built‑in recursive solver animation.
- **Moves**: Shows your current move count.

### Interactions
- **Drag & drop**: Drag the top disk of a peg and drop it on another peg.
- **Click‑to‑move**: Click the top disk to select, then click a destination peg.
- **Keyboard**: Focus a peg (tab to it), press Enter or Space to select/deselect/move like click‑to‑move.

### Accessibility
- Pegs are focusable and labeled via `aria-label`.
- Announcements are provided via the `#message` region with `aria-live="polite"`.

### Customization
- **Disk colors**: Edit the `diskColors` array inside `twitter.html` to change the palette.
- **Auto‑solve speed**: Change the delay in `sleep(500)` to a different value (milliseconds).
- **Default disk count**: Update the `value` attribute of the `#diskCount` input.

### Programmatic examples (via the DOM)
- Start auto‑solve:
  ```js
  document.getElementById('autoSolveBtn').click();
  ```
- Reset with a specific disk count:
  ```js
  const input = document.getElementById('diskCount');
  input.value = 5; // 3..10
  input.dispatchEvent(new Event('change', { bubbles: true }));
  ```

For a full reference of internal functions, UI components, events, and state, see the API docs.

- See: `docs/API.md`