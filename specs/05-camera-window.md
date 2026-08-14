# 05 — Camera window

**Status:** Implemented

## Context

The **Camera** preview window originally opened at the webcam's native
capture resolution with a fixed size, which is often too large for a
corner-of-screen OBS capture setup.

## Requirements

1. The **Camera** window SHALL be created with `cv2.WINDOW_NORMAL` (user
   resizable via dragging any edge/corner), not the default fixed-size mode.
2. The **Camera** window SHALL open at a smaller default size (480×360)
   rather than the webcam's native resolution.

## Test coverage

None — this is a pure OpenCV window-manager call with no return value or
observable state outside the actual OS window; not unit-testable. See
Manual validation.

## Manual validation

- [ ] On launch, the Camera window opens noticeably smaller than a typical
      webcam frame.
- [ ] Dragging a corner of the Camera window resizes it.
