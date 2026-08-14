# 06 — Gesture confidence threshold

**Status:** Implemented

## Context

`GestureRecognizer` only commits to a category above a confidence score; by
default this required a fairly clean, "textbook" gesture, so a
less-than-perfect gesture in front of the camera would just fall back to
neutral. Users need to be able to loosen (or tighten) that bar to trade
tolerance against the risk of confusing two similar gestures.

## Requirements

1. `main()` SHALL accept a `gesture_threshold: float` parameter (default
   `DEFAULT_GESTURE_THRESHOLD = 0.5`) and pass it as
   `canned_gesture_classifier_options=ClassifierOptions(score_threshold=...)`
   to `GestureRecognizerOptions`.
2. The CLI SHALL expose this as `--gesture-threshold`, documented with the
   default value in its help text.
3. Lowering the threshold SHALL accept gestures MediaPipe scores less
   confidently (more tolerant, more false-positive risk); raising it SHALL
   require a cleaner match (stricter, more false-negative risk). This is a
   pass-through to MediaPipe's own scoring — not re-implemented here.

## Test coverage

None directly — this only configures a third-party classifier's internal
threshold; there's no app-level decision logic to unit test (see
`resolve_gesture`/`GestureLabels` tests in
[01-gesture-recognition.md](01-gesture-recognition.md) for what happens
*after* MediaPipe returns a category). Covered by the `--gesture-threshold`
argparse wiring being exercised via `python gesture_display.py --help`.

## Manual validation

- [ ] `--gesture-threshold 0.3` recognizes gestures done less precisely than
      the default.
- [ ] `--gesture-threshold 0.8` requires cleaner gestures and reduces
      cross-gesture confusion.
