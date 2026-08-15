# 02 — Idle / neutral state

**Status:** Implemented

## Context

Originally, when no gesture was detected the app just kept showing the last
recognized gesture's image forever — there was no way to tell "no hand" from
"still doing the last gesture". A `neutre` state was added, and — like every
other gesture — it needed to be debounced, so a single ambiguous or dropped
frame doesn't cause visible flicker.

The debounce was initially frame-count based (`DEBOUNCE_FRAMES = 4`
consecutive `update()` calls). That's not a reliable "hold the gesture for a
moment" guarantee — 4 frames is ~130ms at 30fps but only ~66ms at 60fps, so
the actual hold time silently depends on the camera/machine's frame rate. It
was changed to a wall-clock hold duration instead, so "hold the gesture for
about a second before it switches" means the same thing everywhere.

## Requirements

1. There SHALL be a `NEUTRAL_GESTURE` key (`"neutre"`) that is displayed when
   no gesture is confidently recognized.
2. `GestureDebouncer` SHALL start in the neutral state.
3. A candidate gesture (including neutral) SHALL only become the displayed
   `current` gesture after being observed continuously for at least
   `hold_seconds` of wall-clock time (default `DEFAULT_HOLD_SECONDS = 1.0`),
   not a frame count.
4. `GestureDebouncer` SHALL accept an injectable `clock` callable (defaulting
   to `time.monotonic`) so hold duration is testable without real delays.
5. A change to a different candidate SHALL reset the hold timer for that new
   candidate — time spent on the previous candidate does not carry over.
6. `current` SHALL only ever change when a candidate has been held for
   `hold_seconds` — it never reverts on its own between updates.
7. The CLI SHALL expose this as `--hold-seconds`, documented with the
   default value in its help text.

## Test coverage

`tests/test_gesture_display.py::TestGestureDebouncer`

## Manual validation

- [ ] Removing your hand from frame makes the Image window settle back to
      the neutral placeholder after roughly one second, not instantly and
      not stuck on the last gesture forever.
- [ ] Switching from one gesture straight to another (no gap) takes about a
      second to register the new one, regardless of how fast the webcam
      captures frames.
- [ ] `--hold-seconds 0.3` makes gestures register faster; `--hold-seconds 2`
      requires holding a gesture noticeably longer.
