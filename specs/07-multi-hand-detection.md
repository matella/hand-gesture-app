# 07 — Multi-hand detection

**Status:** Implemented

## Context

The app originally tracked a single hand (`num_hands=1`), so if two hands
were in frame only one was ever considered. The reels that inspired this
project's assets track both hands. Extended to `num_hands=2` so either hand
can independently trigger a gesture.

## Requirements

1. `GestureRecognizerOptions` SHALL be configured with `num_hands=2`.
2. `resolve_gesture(result)` SHALL check each detected hand, in the order
   MediaPipe returns them, and return the first one whose top category maps
   to a known gesture via `GESTURE_LABELS`.
3. If the first hand's top category is unmapped (e.g. `Thumb_Down`) but a
   second hand's is mapped, `resolve_gesture` SHALL return the second hand's
   gesture — an unmapped first hand does not block a mapped second hand.
4. If no hand has a mapped gesture (including zero hands detected),
   `resolve_gesture` SHALL return `None`, same as the single-hand case.
5. There is no "combo" logic — two hands showing two different mapped
   gestures simultaneously does not produce a distinct third result; the
   first-in-order mapped hand simply wins. This is a deliberate scope
   decision, not a limitation to fix later.
6. Landmarks SHALL be drawn on the Camera window for every detected hand,
   not just the one that wins gesture resolution.

## Test coverage

`tests/test_gesture_display.py::TestResolveGesture` (multi-hand cases)

## Manual validation

- [ ] Holding up two hands with different recognized gestures shows one of
      them (not a crash, not a blend).
- [ ] Both hands' landmark dots are drawn on the Camera window at once.
