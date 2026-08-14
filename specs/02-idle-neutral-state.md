# 02 — Idle / neutral state

**Status:** Implemented

## Context

Originally, when no gesture was detected the app just kept showing the last
recognized gesture's image forever — there was no way to tell "no hand" from
"still doing the last gesture". A `neutre` state was added, and — like every
other gesture — it needed to be debounced, so a single ambiguous or dropped
frame doesn't cause visible flicker.

## Requirements

1. There SHALL be a `NEUTRAL_GESTURE` key (`"neutre"`) that is displayed when
   no gesture is confidently recognized.
2. `GestureDebouncer` SHALL start in the neutral state.
3. A candidate gesture (including neutral) SHALL only become the displayed
   `current` gesture after being observed on `debounce_frames` consecutive
   `update()` calls (default `DEBOUNCE_FRAMES = 4`).
4. A single interrupting frame SHALL reset the consecutive-match counter for
   the new candidate to 1, not deduct from the previous streak.
5. `current` SHALL only ever change when a candidate reaches the debounce
   threshold — it never reverts on its own between updates.

## Test coverage

`tests/test_gesture_display.py::TestGestureDebouncer`

## Manual validation

- [ ] Removing your hand from frame makes the Image window settle back to
      the neutral placeholder after a brief, non-flickery delay (not
      instantly, not stuck on the last gesture forever).
