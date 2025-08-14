# API Reference: Tower of Hanoi (twitter.html)

This document describes the publicly observable UI, DOM contracts, internal functions, and extension points for the Tower of Hanoi implementation in `twitter.html`.

## Overview
Everything is contained in a self‑invoking script block that binds DOM elements and registers listeners. While functions are not exported as modules, they can be reasoned about and extended via DOM hooks and by modifying the script.

## UI Structure (DOM Contracts)
- `#diskCount` (input[type=number])
  - Range: 3..10
  - Changing value triggers a game reset via the `change` event.
- `#resetBtn` (button)
  - Click to reset the game with the current disk count.
- `#autoSolveBtn` (button)
  - Click to start the auto solver animation.
- `#moveCounter` (div)
  - Displays move count, text format: `Moves: <number>`.
- `#game` (div)
  - Contains three child pegs: `#source`, `#auxiliary`, `#destination`, each with class `peg` and `data-peg="0|1|2"`.
- `.peg` (div)
  - Focusable (`tabindex=0`), `aria-label` set to peg name.
  - Accepts drag over and drop events.
  - Click selects destination when a disk is selected.
- `.disk` (div)
  - Top disks are actionable via drag or click.
  - Attributes: `draggable`, `data-size` (1..N), width proportional to size.
- `#message` (div)
  - `role=alert`, `aria-live=polite` for status messaging (win state, auto‑solve state).

## State Model
- `numDisks: number` — current disk count, clamped to [3, 10].
- `pegsData: number[][]` — three stacks of disk sizes; each entry is the size of a disk, top is the last element.
- `moveCount: number` — number of successful moves performed.
- `selectedDisk: HTMLElement | null` — currently selected `.disk` for click‑to‑move.
- `selectedPegIndex: 0|1|2 | null` — origin peg when using click‑to‑move.
- `isAutoSolving: boolean` — prevents user interaction during solving.
- `dragSourcePeg: 0|1|2 | null` — origin peg for drag‑and‑drop.
- `diskColors: string[]` — color palette; disks use `(diskSize - 1) % diskColors.length`.

## Key Functions
Note: These functions are defined inside an IIFE and are not exported globally. Use them as reference for behavior or expose them manually if needed.

- `initGame(): void`
  - Resets state from `#diskCount`, repopulates `pegsData`, resets `moveCount`, clears selection, renders.
  - Side effects: Updates UI, message, move counter.
  - Example (trigger via UI):
    ```js
    document.getElementById('resetBtn').click();
    ```

- `render(): void`
  - Rebuilds `.disk` elements for each `.peg` from `pegsData` and (re)attaches event handlers.
  - Highlights top disks via `highlightMovableDisks()`.

- `highlightMovableDisks(): void`
  - Adds a glow to movable top disks and sets pointer cursor.

- `moveDisk(fromPeg: 0|1|2, toPeg: 0|1|2): boolean`
  - Validates and performs a move if legal (no larger on smaller).
  - Increments `moveCount`, re‑renders, checks win condition.
  - Returns true on success.
  - Example (programmatic move):
    ```js
    // Move top disk from Source(0) to Destination(2)
    // Not exported; see Extension: exposing functions below.
    ```

- `updateMoveCounter(): void`
  - Sets `#moveCounter.textContent` to `Moves: <moveCount>`.

- `checkWin(): void`
  - If `pegsData[2].length === numDisks`, updates message and disables interaction.

- `disableUserInteraction(): void` / `enableUserInteraction(): void`
  - Toggles pointer events and disables/enables controls.

- `autoSolve(n: number, from: 0|1|2, to: 0|1|2, aux: 0|1|2): Promise<void>`
  - Recursive Tower of Hanoi solution. Uses `sleep(500)` between moves while `isAutoSolving`.
  - Contract: expects `isAutoSolving === true` to animate; otherwise it will not enqueue user input.

- `sleep(ms: number): Promise<void>`
  - Utility delay.

- `startAutoSolve(): Promise<void>`
  - Sets `isAutoSolving`, disables interaction, updates message, runs `autoSolve`, then re‑enables interaction and shows result.
  - Example:
    ```js
    document.getElementById('autoSolveBtn').click();
    ```

- Event handlers
  - `onDragStart`, `onDragEnd`, `onDragOver`, `onDragLeave`, `onDrop`
  - `onDiskClick`, `onPegClick`
  - Keyboard: keydown on `.peg` to synthesize click for Enter/Space.

## Events and User Flows
- Changing `#diskCount` triggers `initGame()` via `change` listener and input clamping.
- Clicking `#resetBtn` triggers `initGame()`.
- Clicking `#autoSolveBtn` triggers `startAutoSolve()`.
- Winning state triggers `messageEl.textContent = "🎉 You solved it in X moves!"` and disables interaction until the next reset.

## Styling Hooks
- `.disk-color-<0..9>` classes are applied to disks; you can override in CSS.
- `.peg.drag-over` is applied while a disk is dragged over a peg.
- `.disk.dragging` while dragging.

## Examples
- Set disk count and reset:
  ```js
  const input = document.getElementById('diskCount');
  input.value = 6;
  input.dispatchEvent(new Event('change', { bubbles: true }));
  ```

- Start auto‑solve:
  ```js
  document.getElementById('autoSolveBtn').click();
  ```

- Focus pegs via keyboard and use Enter/Space to move:
  ```js
  document.getElementById('source').focus();
  // Press Enter or Space to select/move.
  ```

## Extension: exposing functions for programmatic control
By default, functions are scoped to the IIFE. If you need to call them programmatically (e.g., in tests), expose a minimal API by attaching to `window`:

```html
<script>
(() => {
  // ...existing code...
  window.hanoi = {
    reset: initGame,
    start: startAutoSolve,
    move: moveDisk,
    get state() {
      return { numDisks, pegsData: pegsData.map(a => a.slice()), moveCount };
    }
  };
})();
</script>
```

Then you can do:
```js
window.hanoi.reset();
window.hanoi.move(0, 2);
console.log(window.hanoi.state.moveCount);
```

## Notes
- The implementation guards against interaction during auto‑solve using `isAutoSolving`.
- `autoSolve` uses a fixed delay of 500ms. Reduce for faster animation.