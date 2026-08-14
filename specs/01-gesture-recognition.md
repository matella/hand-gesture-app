# 01 — Gesture recognition

**Status:** Implemented

## Context

The app captures webcam frames and must classify the user's hand into one of
a small set of known gestures, so a matching image can be displayed.

An earlier version used a hand-rolled heuristic (finger-tip vs. joint
Y-coordinate comparisons). It was dropped because it was orientation-
dependent and unreliable — e.g. a closed fist was frequently misread as an
open hand when the hand was rotated. It's replaced by MediaPipe's
pretrained `GestureRecognizer` task, which classifies against a fixed,
trained vocabulary of 8 categories: `None`, `Closed_Fist`, `Open_Palm`,
`Pointing_Up`, `Thumb_Down`, `Thumb_Up`, `Victory`, `ILoveYou`.

## Requirements

1. The system SHALL classify at most one hand per frame (`num_hands=1`).
2. The system SHALL map recognized categories to internal gesture keys via
   `GESTURE_LABELS`:
   - `Closed_Fist` → `poing`
   - `Open_Palm` → `main_ouverte`
   - `Victory` → `peace`
   - `Thumb_Up` → `pouce`
   - `Pointing_Up` → `shush`
3. `Thumb_Down`, `ILoveYou`, and `None` SHALL NOT be mapped to a gesture —
   `resolve_gesture` returns `None` for them, which the caller treats as "no
   gesture this frame" (see [02-idle-neutral-state.md](02-idle-neutral-state.md)).
4. If no hand is detected in a frame (`result.hand_landmarks` empty),
   `resolve_gesture` SHALL return `None` regardless of `result.gestures`.
5. Every value in `GESTURE_LABELS` SHALL be a valid key in `GESTURE_IMAGES`
   (a mapped gesture must always have a displayable image).

## Known limitation

`Thumb_Down` is deliberately unmapped: it's visually close to `Closed_Fist`
(the model sometimes confuses the two based on thumb position), and there is
no dedicated "shaka" image to justify a mapping — see chat history for the
original `swag.gif` mapping that was removed for causing a misleading
fist → shaka mismatch.

## Test coverage

`tests/test_gesture_display.py::TestResolveGesture`,
`TestGestureLabelsConsistency`

## Manual validation

- [ ] Making a fist consistently shows the `poing` image within ~1s.
- [ ] Doing a `Thumb_Down` (fist, thumb pointing down) does not show a
      random unrelated image — it falls back to neutral.
