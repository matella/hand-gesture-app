# 08 — Facial expression detection

**Status:** Implemented

## Context

Extends the app beyond hand gestures with a second MediaPipe task,
`FaceLandmarker` (with `output_face_blendshapes=True`), so simple facial
expressions can also trigger a display image — same overall idea as hand
gestures, but blendshapes are continuous 0-1 scores per facial movement
rather than a single classified category, so each expression needs its own
threshold rule instead of a lookup table.

## Requirements

1. `FaceLandmarkerOptions` SHALL be configured with `num_faces=1` and
   `output_face_blendshapes=True`.
2. `resolve_expression(result)` SHALL take a `FaceLandmarkerResult`-shaped
   object and return one of the `EXPRESSION_KEYS` gesture keys, or `None` if
   no face is detected or no rule's threshold is met.
3. Supported expressions and their rule, checked in this fixed priority
   order (first match wins — order chosen so the most distinct/least
   false-positive-prone expressions are checked first):
   1. **`surprise`** — `jawOpen` ≥ `MOUTH_OPEN_THRESHOLD` (mouth open)
   2. **`smile`** — average of `mouthSmileLeft`/`mouthSmileRight` ≥
      `SMILE_THRESHOLD`
   3. **`wink`** — one eye's blink score ≥ `WINK_CLOSED_THRESHOLD` while the
      other's is < `WINK_OPEN_THRESHOLD` (asymmetric, to distinguish a wink
      from a normal two-eye blink)
   4. **`eyebrows`** — average of `browInnerUp`/`browOuterUpLeft`/
      `browOuterUpRight` ≥ `EYEBROWS_THRESHOLD`
4. All four expression keys SHALL be present in `GESTURE_IMAGES` — face
   expressions and hand gestures share the same display pipeline and image
   namespace, they just come from a different detector.
5. **Hands take priority over face.** In `main()`, the frame's displayed
   gesture SHALL be `resolve_gesture(hand_result) or resolve_expression(face_result)`
   — a recognized hand gesture always wins over a simultaneously detected
   facial expression. There is no combined hand+face state.
6. `ensure_model` (see [04-model-provisioning.md](04-model-provisioning.md))
   SHALL be reused as-is for the face model, called with
   `FACE_MODEL_PATH`/`FACE_MODEL_URL`, since it's already parameterized.

## Known limitation

The exact blendshape category name strings (`jawOpen`, `mouthSmileLeft`,
`eyeBlinkLeft`, `browInnerUp`, etc.) are taken from MediaPipe's official
documentation, which states they follow the ARKit blendshape naming
convention. This project has no way to run a real face through the model in
this environment to empirically confirm the exact strings returned at
runtime — see the manual validation checklist below.

Running two ML models per frame (`GestureRecognizer` + `FaceLandmarker`)
roughly doubles the per-frame CPU cost compared to hands-only.

## Test coverage

`tests/test_gesture_display.py::TestResolveExpression`

## Manual validation

- [ ] Smiling shows the `smile` image.
- [ ] Opening your mouth shows the `surprise` image.
- [ ] Winking one eye shows the `wink` image (and a normal two-eye blink
      does NOT trigger it).
- [ ] Raising your eyebrows shows the `eyebrows` image.
- [ ] Making a hand gesture while also smiling shows the hand gesture's
      image, not the face one.
- [ ] If blendshape scores don't behave as expected, check the actual
      `category_name` strings MediaPipe returns at runtime (e.g. print
      `result.face_blendshapes[0]`) against the names hardcoded in
      `resolve_expression` — see Known limitation above.
