# 03 — Gesture asset loading

**Status:** Implemented

## Context

Each gesture key in `GESTURE_IMAGES` points to an image file in `assets/`.
These are user-customizable (see README "Personnaliser les images"), so a
missing or corrupt file is expected to happen occasionally and must not
crash the app.

## Requirements

1. `load_overlays(gesture_images)` SHALL return a dict of only the
   successfully loaded images, keyed by gesture name.
2. A file that `cv2.imread` cannot read (missing path, corrupt file,
   unsupported format) SHALL be skipped, with a warning printed to stdout
   containing the gesture name and the attempted path — not raise.
3. One unreadable entry SHALL NOT prevent the other entries from loading.
4. Any format `cv2.imread` supports is acceptable (`.png`, `.jpg`, `.gif`,
   `.bmp`, `.webp`, ...). For animated `.gif` files, only the first frame is
   read — the app has no frame-animation support.

## Test coverage

`tests/test_gesture_display.py::TestLoadOverlays`
