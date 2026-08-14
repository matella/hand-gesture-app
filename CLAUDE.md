# hand-gesture-app

## Workflow: spec-driven, test-first

This project is developed spec-first, test-first. For any behavior change:

1. Write/update a spec in `specs/` before writing implementation code.
2. Write a failing test in `tests/` that encodes the spec's acceptance
   criteria.
3. Implement the minimum code to make it pass.
4. Refactor with the suite green.

Full process and the current spec index: [`specs/README.md`](specs/README.md).

Run tests: `pytest` (from repo root; needs `pip install -r requirements-dev.txt`).

Not everything is unit-testable — `gesture_display.main()` is a live webcam
+ OpenCV-window loop. Keep it as thin glue over testable units
(`resolve_gesture`, `GestureDebouncer`, `load_overlays`, `ensure_model`);
put decision logic in those units, not in the loop, so it stays testable.
For the loop itself, each spec lists a manual validation checklist instead.
