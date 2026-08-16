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


class FakeClock:
    """Horloge manuelle pour tester GestureDebouncer sans vraies attentes."""

    def __init__(self, start: float = 0.0):
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def make_result(*category_names, has_hand=True):
    """Construit un faux GestureRecognizerResult avec une main par nom de
    catégorie fourni (ordre = ordre de détection MediaPipe simulé).

    Sans argument : simule une frame sans main détectée (`has_hand=False`)
    ou une main détectée sans geste scoré (`has_hand=True`, comportement
    par défaut).
    """
    if not category_names:
        return types.SimpleNamespace(
            gestures=[],
            hand_landmarks=[[types.SimpleNamespace(x=0.5, y=0.5)]] if has_hand else [],
        )
    gestures = []
    hand_landmarks = []
    for name in category_names:
        hand_landmarks.append([types.SimpleNamespace(x=0.5, y=0.5)])
        gestures.append([types.SimpleNamespace(category_name=name)] if name else [])
    return types.SimpleNamespace(gestures=gestures, hand_landmarks=hand_landmarks)


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

    # --- specs/07-multi-hand-detection.md ---

    def test_first_hand_with_mapped_gesture_wins(self):
        result = make_result("Victory", "Closed_Fist")
        assert gd.resolve_gesture(result) == "peace"

    def test_falls_through_to_second_hand_when_first_is_unmapped(self):
        result = make_result("Thumb_Down", "Closed_Fist")
        assert gd.resolve_gesture(result) == "poing"

    def test_both_hands_unmapped_returns_none(self):
        result = make_result("Thumb_Down", "ILoveYou")
        assert gd.resolve_gesture(result) is None


class TestGestureLabelsConsistency:
    """Garde-fou de config : toute entrée de GESTURE_LABELS doit pointer
    vers une clé réellement présente dans GESTURE_IMAGES, sous peine
    d'afficher un geste sans overlay associé."""

    def test_every_mapped_gesture_has_an_image_entry(self):
        for gesture_key in gd.GESTURE_LABELS.values():
            assert gesture_key in gd.GESTURE_IMAGES

    def test_neutral_gesture_has_an_image_entry(self):
        assert gd.NEUTRAL_GESTURE in gd.GESTURE_IMAGES

    def test_every_expression_key_has_an_image_entry(self):
        for expression_key in gd.EXPRESSION_KEYS:
            assert expression_key in gd.GESTURE_IMAGES


# --- specs/08-facial-expression-detection.md --------------------------------


def make_face_result(**scores):
    """Construit un faux FaceLandmarkerResult à partir de scores de
    blendshapes nommés (ex: make_face_result(jawOpen=0.9)). Les blendshapes
    non précisés valent 0. Sans argument : simule un visage détecté mais
    neutre (aucune expression active).
    """
    categories = [
        types.SimpleNamespace(category_name=name, score=score)
        for name, score in scores.items()
    ]
    return types.SimpleNamespace(face_blendshapes=[categories])


def make_no_face_result():
    return types.SimpleNamespace(face_blendshapes=[])


class TestResolveExpression:
    def test_no_face_returns_none(self):
        assert gd.resolve_expression(make_no_face_result()) is None

    def test_neutral_face_returns_none(self):
        assert gd.resolve_expression(make_face_result()) is None

    def test_mouth_open_maps_to_surprise(self):
        result = make_face_result(jawOpen=0.9)
        assert gd.resolve_expression(result) == "surprise"

    def test_smile_maps_to_smile(self):
        result = make_face_result(mouthSmileLeft=0.8, mouthSmileRight=0.8)
        assert gd.resolve_expression(result) == "smile"

    def test_asymmetric_eye_blink_maps_to_wink(self):
        result = make_face_result(eyeBlinkLeft=0.9, eyeBlinkRight=0.05)
        assert gd.resolve_expression(result) == "wink"

    def test_symmetric_blink_does_not_map_to_wink(self):
        # Un clignement des deux yeux à la fois n'est pas un wink.
        result = make_face_result(eyeBlinkLeft=0.9, eyeBlinkRight=0.85)
        assert gd.resolve_expression(result) is None

    def test_raised_eyebrows_maps_to_eyebrows(self):
        result = make_face_result(
            browInnerUp=0.7, browOuterUpLeft=0.6, browOuterUpRight=0.6
        )
        assert gd.resolve_expression(result) == "eyebrows"

    def test_mouth_open_takes_priority_over_smile(self):
        # surprise est vérifié avant smile dans l'ordre de priorité.
        result = make_face_result(
            jawOpen=0.9, mouthSmileLeft=0.8, mouthSmileRight=0.8
        )
        assert gd.resolve_expression(result) == "surprise"


# --- specs/02-idle-neutral-state.md -----------------------------------------


class TestGestureDebouncer:
    def test_starts_on_neutral(self):
        deb = gd.GestureDebouncer()
        assert deb.current == gd.NEUTRAL_GESTURE

    def test_does_not_switch_before_hold_duration_elapsed(self):
        clock = FakeClock()
        deb = gd.GestureDebouncer(hold_seconds=1.0, clock=clock)
        deb.update("poing")
        clock.advance(0.9)
        current = deb.update("poing")
        assert current == gd.NEUTRAL_GESTURE

    def test_switches_once_hold_duration_elapsed(self):
        clock = FakeClock()
        deb = gd.GestureDebouncer(hold_seconds=1.0, clock=clock)
        deb.update("poing")
        clock.advance(1.0)
        current = deb.update("poing")
        assert current == "poing"

    def test_switching_target_resets_the_hold_timer(self):
        clock = FakeClock()
        deb = gd.GestureDebouncer(hold_seconds=1.0, clock=clock)
        deb.update("poing")
        clock.advance(0.9)
        deb.update("peace")  # coupe la tenue de "poing" avant le seuil
        clock.advance(0.9)
        deb.update("poing")  # repart de zéro, encore 0.9s < 1.0s
        assert deb.current == gd.NEUTRAL_GESTURE

    def test_missing_hand_eventually_falls_back_to_neutral(self):
        clock = FakeClock()
        deb = gd.GestureDebouncer(hold_seconds=0.5, clock=clock)
        deb.update("poing")
        clock.advance(0.5)
        assert deb.update("poing") == "poing"
        deb.update(None)
        clock.advance(0.5)
        assert deb.update(None) == gd.NEUTRAL_GESTURE

    def test_short_interruption_does_not_immediately_revert_current(self):
        """Une brève interruption ne doit pas faire retomber l'affichage
        tant que le nouveau candidat n'a pas lui-même tenu `hold_seconds`."""
        clock = FakeClock()
        deb = gd.GestureDebouncer(hold_seconds=1.0, clock=clock)
        deb.update("poing")
        clock.advance(1.0)
        assert deb.update("poing") == "poing"
        clock.advance(0.1)
        deb.update(None)  # interruption de 0.1s seulement
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
