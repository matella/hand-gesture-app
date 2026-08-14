# Specs

This project is developed **spec-driven, test-first**:

1. **Spec.** Before changing behavior, write or update a spec here describing
   the requirement and its acceptance criteria.
2. **Red.** Write a failing test in `tests/` that encodes the acceptance
   criteria from the spec.
3. **Green.** Write the minimum implementation code to make the test pass.
4. **Refactor.** Clean up with the test suite green.
5. **Update status.** Mark the spec `Implemented` and link the covering
   tests once it's done.

This workflow is mandatory for this project — see [`/CLAUDE.md`](../CLAUDE.md).

## Index

| Spec | Status | Covers |
|---|---|---|
| [01-gesture-recognition.md](01-gesture-recognition.md) | Implemented | Webcam → gesture classification → image mapping |
| [02-idle-neutral-state.md](02-idle-neutral-state.md) | Implemented | Debounced fallback when no gesture is confidently detected |
| [03-asset-loading.md](03-asset-loading.md) | Implemented | Loading gesture overlay images, missing-file handling |
| [04-model-provisioning.md](04-model-provisioning.md) | Implemented | Auto-download of the MediaPipe model on first run |
| [05-camera-window.md](05-camera-window.md) | Implemented | Resizable Camera preview window |
| [06-gesture-confidence-threshold.md](06-gesture-confidence-threshold.md) | Implemented | Tunable strictness of gesture classification |

## Why some things aren't unit tested

`main()` is a real-time loop over live webcam frames and OpenCV windows —
there's no meaningful way to unit test "does a window open" or "does the
webcam capture a frame" without a real camera and display. The loop is kept
intentionally thin: it wires together the testable units (`resolve_gesture`,
`GestureDebouncer`, `load_overlays`, `ensure_model`) with I/O, and does no
decision-making of its own. Each spec below lists a short **Manual
validation** checklist for the parts that only a human running the app can
actually confirm.
