"""
Tests unitaires pour gesture_display.py.

Ces tests couvrent la logique pure (résolution de geste, debounce,
chargement des overlays, téléchargement du modèle) — pas la boucle
temps réel elle-même (webcam + fenêtres cv2), qui reste vérifiée
manuellement (voir specs/README.md, section "Validation manuelle").

Chaque classe de tests référence la spec qu'elle vérifie ; voir specs/.
"""

import types

import numpy as np
import pytest
import cv2

import gesture_display as gd


def make_result(category_name=None, has_hand=True):
    """Construit un faux GestureRecognizerResult minimal pour les tests.

    `category_name=None` simule une frame sans main détectée.
    """
    if category_name is None:
        return types.SimpleNamespace(
            gestures=[],
            hand_landmarks=[[types.SimpleNamespace(x=0.5, y=0.5)]] if has_hand else [],
        )
    category = types.SimpleNamespace(category_name=category_name)
    return types.SimpleNamespace(
        gestures=[[category]],
        hand_landmarks=[[types.SimpleNamespace(x=0.5, y=0.5)]],
    )


# --- specs/01-gesture-recognition.md ---------------------------------------


class TestResolveGesture:
    def test_no_hand_returns_none(self):
        assert gd.resolve_gesture(make_result(has_hand=False)) is None

    def test_hand_present_but_no_gesture_scored_returns_none(self):
        result = types.SimpleNamespace(
            gestures=[], hand_landmarks=[[types.SimpleNamespace(x=0.5, y=0.5)]]
        )
        assert gd.resolve_gesture(result) is None

    @pytest.mark.parametrize(
        "category_name,expected",
        [
            ("Closed_Fist", "poing"),
            ("Open_Palm", "main_ouverte"),
            ("Victory", "peace"),
            ("Thumb_Up", "pouce"),
            ("Pointing_Up", "shush"),
        ],
    )
    def test_known_category_maps_to_gesture(self, category_name, expected):
        assert gd.resolve_gesture(make_result(category_name)) == expected

    @pytest.mark.parametrize("category_name", ["None", "Thumb_Down", "ILoveYou"])
    def test_unmapped_category_returns_none(self, category_name):
        # Thumb_Down est volontairement non mappé (cf. specs/01) : trop
        # proche visuellement de Closed_Fist pour avoir sa propre image.
        assert gd.resolve_gesture(make_result(category_name)) is None


class TestGestureLabelsConsistency:
    """Garde-fou de config : toute entrée de GESTURE_LABELS doit pointer
    vers une clé réellement présente dans GESTURE_IMAGES, sous peine
    d'afficher un geste sans overlay associé."""

    def test_every_mapped_gesture_has_an_image_entry(self):
        for gesture_key in gd.GESTURE_LABELS.values():
            assert gesture_key in gd.GESTURE_IMAGES

    def test_neutral_gesture_has_an_image_entry(self):
        assert gd.NEUTRAL_GESTURE in gd.GESTURE_IMAGES


# --- specs/02-idle-neutral-state.md -----------------------------------------


class TestGestureDebouncer:
    def test_starts_on_neutral(self):
        deb = gd.GestureDebouncer()
        assert deb.current == gd.NEUTRAL_GESTURE

    def test_does_not_switch_before_threshold(self):
        deb = gd.GestureDebouncer(debounce_frames=4)
        for _ in range(3):
            current = deb.update("poing")
        assert current == gd.NEUTRAL_GESTURE

    def test_switches_once_threshold_reached(self):
        deb = gd.GestureDebouncer(debounce_frames=4)
        for _ in range(4):
            current = deb.update("poing")
        assert current == "poing"

    def test_interrupted_streak_resets_the_counter(self):
        deb = gd.GestureDebouncer(debounce_frames=4)
        deb.update("poing")
        deb.update("poing")
        deb.update("peace")  # casse la série de "poing"
        deb.update("poing")
        deb.update("poing")
        # seulement 2 "poing" consécutifs depuis l'interruption : pas assez
        assert deb.current == gd.NEUTRAL_GESTURE

    def test_missing_hand_eventually_falls_back_to_neutral(self):
        deb = gd.GestureDebouncer(debounce_frames=2)
        deb.update("poing")
        deb.update("poing")
        assert deb.current == "poing"
        deb.update(None)
        deb.update(None)
        assert deb.current == gd.NEUTRAL_GESTURE

    def test_single_flicker_frame_does_not_reset_current(self):
        """Un seul frame ambigu au milieu d'un geste stable ne doit pas
        faire retomber l'affichage tant que le nouveau target n'a pas
        lui-même atteint le seuil de debounce."""
        deb = gd.GestureDebouncer(debounce_frames=3)
        deb.update("poing")
        deb.update("poing")
        deb.update("poing")
        assert deb.current == "poing"
        deb.update(None)  # 1 frame de flicker (pending_count repart à 1)
        assert deb.current == "poing"


# --- specs/03-asset-loading.md ----------------------------------------------


class TestLoadOverlays:
    def test_loads_existing_readable_image(self, tmp_path):
        img_path = tmp_path / "test.png"
        cv2.imwrite(str(img_path), np.zeros((10, 10, 3), dtype=np.uint8))

        overlays = gd.load_overlays({"test": str(img_path)})

        assert "test" in overlays
        assert overlays["test"].shape == (10, 10, 3)

    def test_skips_missing_file_with_warning(self, tmp_path, capsys):
        missing_path = tmp_path / "missing.png"

        overlays = gd.load_overlays({"missing": str(missing_path)})

        assert "missing" not in overlays
        assert "introuvable" in capsys.readouterr().out

    def test_partial_failure_does_not_drop_other_entries(self, tmp_path):
        ok_path = tmp_path / "ok.png"
        cv2.imwrite(str(ok_path), np.zeros((5, 5, 3), dtype=np.uint8))
        missing_path = tmp_path / "missing.png"

        overlays = gd.load_overlays({"ok": str(ok_path), "missing": str(missing_path)})

        assert set(overlays) == {"ok"}


# --- specs/04-model-provisioning.md -----------------------------------------


class TestEnsureModel:
    def test_does_not_download_when_model_already_present(self, tmp_path):
        model_path = tmp_path / "model.task"
        model_path.write_bytes(b"fake-model-bytes")
        calls = []

        gd.ensure_model(
            model_path=str(model_path),
            model_url="http://example.invalid/model.task",
            downloader=lambda url, path: calls.append((url, path)),
        )

        assert calls == []

    def test_downloads_and_creates_parent_dir_when_missing(self, tmp_path):
        model_path = tmp_path / "nested" / "model.task"
        calls = []

        def fake_downloader(url, path):
            calls.append((url, path))
            with open(path, "wb") as f:
                f.write(b"fake-model-bytes")

        gd.ensure_model(
            model_path=str(model_path),
            model_url="http://example.invalid/model.task",
            downloader=fake_downloader,
        )

        assert calls == [("http://example.invalid/model.task", str(model_path))]
        assert model_path.exists()
