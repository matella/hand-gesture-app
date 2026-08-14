# 04 — Model provisioning

**Status:** Implemented

## Context

`GestureRecognizer` requires a `.task` model bundle (~8 MB) that isn't
practical to commit to the repo. It's fetched from Google's public model
bucket on first run instead, into the git-ignored `models/` directory.

## Requirements

1. `ensure_model(model_path, model_url, downloader)` SHALL be a no-op if
   `model_path` already exists — no network call.
2. If `model_path` does not exist, it SHALL create the parent directory
   (`os.makedirs(..., exist_ok=True)`) and call `downloader(model_url,
   model_path)` exactly once.
3. `downloader` SHALL default to `urllib.request.urlretrieve`, but be
   injectable so tests never perform a real network request.
4. Progress SHALL be communicated via stdout prints (download start /
   completion) — this is a slow, one-time operation and silent hangs are
   confusing.

## Test coverage

`tests/test_gesture_display.py::TestEnsureModel`

## Manual validation

- [ ] Deleting `models/` and re-running the app re-downloads the model
      automatically before the camera opens.
