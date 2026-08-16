"""
Détecte la position de la main via la webcam (MediaPipe GestureRecognizer) et
affiche une image différente selon le geste reconnu : poing, main ouverte,
peace, pouce.

Installation :
    pip install opencv-python mediapipe

Lancement :
    python gesture_display.py
    (touche 'q' pour quitter)

Note : mediapipe >= 1.0.0 a remplacé l'ancienne API `mp.solutions.hands` par
la Tasks API. On utilise ici `GestureRecognizer`, un classifieur pré-entraîné
(plus précis qu'une heuristique géométrique maison), qui nécessite un modèle
`.task` téléchargé séparément. Ce script le télécharge automatiquement au
premier lancement dans le dossier `models/`.
"""

import argparse
import os
import time
import urllib.request

import cv2
import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.components.processors.classifier_options import (
    ClassifierOptions,
)
from mediapipe.tasks.python.core.base_options import BaseOptions
from mediapipe.tasks.python.vision.drawing_utils import draw_landmarks

# --- Config ---------------------------------------------------------------

# Résolu par rapport à l'emplacement du script, pas au dossier d'exécution.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# Durée (en secondes) pendant laquelle un geste doit être tenu sans
# interruption avant que l'image affichée ne change. Basé sur le temps réel
# plutôt qu'un nombre de frames, pour un ressenti constant quel que soit le
# framerate de la webcam.
DEFAULT_HOLD_SECONDS = 1.0

# Score de confiance minimum (0-1) pour qu'un geste soit retenu plutôt que de
# retomber sur "neutre". Plus bas = reconnaît des gestes moins "parfaits"
# (mais augmente le risque de confondre deux gestes proches).
DEFAULT_GESTURE_THRESHOLD = 0.5

MODEL_PATH = os.path.join(BASE_DIR, "models", "gesture_recognizer.task")
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/gesture_recognizer/"
    "gesture_recognizer/float16/latest/gesture_recognizer.task"
)

FACE_MODEL_PATH = os.path.join(BASE_DIR, "models", "face_landmarker.task")
FACE_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
    "face_landmarker/float16/latest/face_landmarker.task"
)

# Seuils (0-1) des scores de blendshapes MediaPipe au-delà desquels une
# expression faciale est considérée active. Voir specs/08.
MOUTH_OPEN_THRESHOLD = 0.5
SMILE_THRESHOLD = 0.5
WINK_CLOSED_THRESHOLD = 0.5
WINK_OPEN_THRESHOLD = 0.3
EYEBROWS_THRESHOLD = 0.4

# Clés d'expression faciale (voir resolve_expression) devant chacune avoir
# une entrée dans GESTURE_IMAGES.
EXPRESSION_KEYS = ["surprise", "smile", "wink", "eyebrows"]

GESTURE_IMAGES = {
    "poing": os.path.join(ASSETS_DIR, "fist.gif"),
    "main_ouverte": os.path.join(ASSETS_DIR, "main_ouverte.png"),
    "peace": os.path.join(ASSETS_DIR, "peace.png"),
    "pouce": os.path.join(ASSETS_DIR, "pouce.png"),
    "shush": os.path.join(ASSETS_DIR, "shush.gif"),
    "surprise": os.path.join(ASSETS_DIR, "surprise.png"),
    "smile": os.path.join(ASSETS_DIR, "smile.png"),
    "wink": os.path.join(ASSETS_DIR, "wink.png"),
    "eyebrows": os.path.join(ASSETS_DIR, "eyebrows.png"),
    "neutre": os.path.join(ASSETS_DIR, "default.jpg"),
}

# Geste affiché quand aucune main n'est détectée ou que la pose est ambiguë.
NEUTRAL_GESTURE = "neutre"

HAND_CONNECTIONS = vision.HandLandmarksConnections.HAND_CONNECTIONS

# Correspondance entre les gestes prédéfinis reconnus par le modèle
# GestureRecognizer (catégories : None, Closed_Fist, Open_Palm, Pointing_Up,
# Thumb_Down, Thumb_Up, Victory, ILoveYou) et les clés de GESTURE_IMAGES.
# Thumb_Down n'est pas mappé : visuellement proche de Closed_Fist (le modèle
# les confond selon la position du pouce), et il n'y a pas d'image shaka
# dédiée — un fist mal reconnu comme Thumb_Down retombe donc sur "neutre"
# plutôt que d'afficher une image trompeuse.
GESTURE_LABELS = {
    "Closed_Fist": "poing",
    "Open_Palm": "main_ouverte",
    "Victory": "peace",
    "Thumb_Up": "pouce",
    "Pointing_Up": "shush",
}


def ensure_model(model_path=MODEL_PATH, model_url=MODEL_URL, downloader=urllib.request.urlretrieve):
    """Télécharge le modèle GestureRecognizer s'il n'est pas déjà présent.

    `downloader` est injectable (signature `(url, path)`) pour pouvoir être
    remplacé par un double de test sans faire de vrai appel réseau.
    """
    if os.path.exists(model_path):
        return
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    print("Téléchargement du modèle GestureRecognizer (première utilisation)...")
    downloader(model_url, model_path)
    print(f"Modèle téléchargé dans {model_path}")


def load_overlays(gesture_images: dict) -> dict:
    """Charge en mémoire les images associées à chaque geste.

    Un fichier manquant ou illisible par `cv2.imread` est ignoré (avec un
    avertissement) plutôt que de faire planter l'appli : le geste retombera
    simplement sur `neutre` faute d'overlay disponible.
    """
    overlays = {}
    for name, path in gesture_images.items():
        img = cv2.imread(path)
        if img is not None:
            overlays[name] = img
        else:
            print(f"Avertissement : image introuvable pour '{name}' ({path})")
    return overlays


def resolve_gesture(result) -> str | None:
    """Retourne la clé GESTURE_IMAGES du geste détecté sur cette frame.

    Jusqu'à deux mains peuvent être détectées (cf. specs/07) : chacune est
    examinée dans l'ordre renvoyé par MediaPipe, et la première dont le
    geste a une entrée dans GESTURE_LABELS gagne — une première main dont le
    geste n'est pas mappé (ex: Thumb_Down) n'empêche pas la seconde de
    déclencher un affichage. Retourne None si aucune main n'a de geste mappé
    (y compris si aucune main n'est détectée du tout).
    """
    for hand_gestures in result.gestures:
        if not hand_gestures:
            continue
        mapped = GESTURE_LABELS.get(hand_gestures[0].category_name)
        if mapped:
            return mapped
    return None


def resolve_expression(result) -> str | None:
    """Retourne la clé GESTURE_IMAGES de l'expression faciale détectée sur
    cette frame, à partir d'un FaceLandmarkerResult (avec
    output_face_blendshapes=True).

    Contrairement aux gestes de la main, les blendshapes sont des scores
    continus (0-1) par mouvement du visage, pas une catégorie unique déjà
    classifiée : chaque expression est donc définie par une règle de seuil,
    évaluée dans un ordre de priorité fixe (voir specs/08). Retourne None si
    aucun visage n'est détecté ou qu'aucune règle ne matche.
    """
    if not result.face_blendshapes:
        return None
    scores = {c.category_name: c.score for c in result.face_blendshapes[0]}

    if scores.get("jawOpen", 0.0) >= MOUTH_OPEN_THRESHOLD:
        return "surprise"

    smile = (scores.get("mouthSmileLeft", 0.0) + scores.get("mouthSmileRight", 0.0)) / 2
    if smile >= SMILE_THRESHOLD:
        return "smile"

    blink_left = scores.get("eyeBlinkLeft", 0.0)
    blink_right = scores.get("eyeBlinkRight", 0.0)
    winking = (
        blink_left >= WINK_CLOSED_THRESHOLD and blink_right < WINK_OPEN_THRESHOLD
    ) or (blink_right >= WINK_CLOSED_THRESHOLD and blink_left < WINK_OPEN_THRESHOLD)
    if winking:
        return "wink"

    eyebrows = (
        scores.get("browInnerUp", 0.0)
        + scores.get("browOuterUpLeft", 0.0)
        + scores.get("browOuterUpRight", 0.0)
    ) / 3
    if eyebrows >= EYEBROWS_THRESHOLD:
        return "eyebrows"

    return None


class GestureDebouncer:
    """Stabilise le geste affiché : ne bascule sur un nouveau geste (ou sur
    le neutre) que lorsqu'il est tenu sans interruption pendant au moins
    `hold_seconds`, pour éviter le flicker sur une détection instable et
    donner un vrai temps de "maintien" avant le changement d'image.

    `clock` est injectable (signature `() -> float`) pour pouvoir tester le
    minutage sans vraies attentes.
    """

    def __init__(
        self,
        hold_seconds: float = DEFAULT_HOLD_SECONDS,
        neutral: str = NEUTRAL_GESTURE,
        clock=time.monotonic,
    ):
        self.hold_seconds = hold_seconds
        self.neutral = neutral
        self.clock = clock
        self.current = neutral
        self._pending = neutral
        self._pending_since = clock()

    def update(self, gesture: str | None) -> str:
        """Prend le geste détecté sur la frame courante (None = pas de main
        détectée ou geste non reconnu) et retourne le geste stabilisé."""
        target = gesture or self.neutral
        now = self.clock()

        if target != self._pending:
            self._pending = target
            self._pending_since = now

        if now - self._pending_since >= self.hold_seconds:
            self.current = target
        return self.current


def main(
    camera_index: int = 0,
    gesture_threshold: float = DEFAULT_GESTURE_THRESHOLD,
    hold_seconds: float = DEFAULT_HOLD_SECONDS,
):
    ensure_model()
    ensure_model(model_path=FACE_MODEL_PATH, model_url=FACE_MODEL_URL)

    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print(f"Impossible d'ouvrir la webcam (index {camera_index}).")
        return

    # Fenêtre redimensionnable (glisser un coin), ouverte en plus petit par défaut.
    cv2.namedWindow("Camera", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Camera", 480, 360)

    overlays = load_overlays(GESTURE_IMAGES)

    options = vision.GestureRecognizerOptions(
        base_options=BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=vision.RunningMode.VIDEO,
        num_hands=2,
        min_hand_detection_confidence=0.7,
        min_tracking_confidence=0.6,
        canned_gesture_classifier_options=ClassifierOptions(
            score_threshold=gesture_threshold
        ),
    )
    face_options = vision.FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=FACE_MODEL_PATH),
        running_mode=vision.RunningMode.VIDEO,
        num_faces=1,
        output_face_blendshapes=True,
    )

    start_time = time.monotonic()
    debouncer = GestureDebouncer(hold_seconds=hold_seconds)

    with vision.GestureRecognizer.create_from_options(options) as recognizer, \
            vision.FaceLandmarker.create_from_options(face_options) as face_landmarker:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            timestamp_ms = int((time.monotonic() - start_time) * 1000)
            result = recognizer.recognize_for_video(mp_image, timestamp_ms)
            face_result = face_landmarker.detect_for_video(mp_image, timestamp_ms)

            # Les mains ont priorité sur le visage (cf. specs/08).
            gesture = resolve_gesture(result) or resolve_expression(face_result)
            for hand_landmarks in result.hand_landmarks:
                draw_landmarks(frame, hand_landmarks, HAND_CONNECTIONS)

            current_gesture = debouncer.update(gesture)

            cv2.putText(
                frame,
                current_gesture,
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2,
            )

            cv2.imshow("Camera", frame)

            if current_gesture in overlays:
                display_img = cv2.resize(overlays[current_gesture], (480, 360))
                cv2.imshow("Image", display_img)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
            if cv2.getWindowProperty("Camera", cv2.WND_PROP_VISIBLE) < 1:
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--camera", type=int, default=0, help="Index de la webcam à utiliser (défaut : 0)"
    )
    parser.add_argument(
        "--gesture-threshold",
        type=float,
        default=DEFAULT_GESTURE_THRESHOLD,
        help=(
            "Score de confiance minimum (0-1) pour valider un geste "
            f"(défaut : {DEFAULT_GESTURE_THRESHOLD}). Plus bas = plus tolérant."
        ),
    )
    parser.add_argument(
        "--hold-seconds",
        type=float,
        default=DEFAULT_HOLD_SECONDS,
        help=(
            "Durée (en secondes) pendant laquelle un geste doit être tenu "
            f"avant de changer l'image affichée (défaut : {DEFAULT_HOLD_SECONDS})."
        ),
    )
    args = parser.parse_args()
    main(
        camera_index=args.camera,
        gesture_threshold=args.gesture_threshold,
        hold_seconds=args.hold_seconds,
    )
