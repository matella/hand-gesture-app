"""
Détecte la position de la main via la webcam (MediaPipe Hands) et affiche
une image différente selon le geste reconnu : poing, main ouverte, peace, pouce.

Installation :
    pip install opencv-python mediapipe

Lancement :
    python gesture_display.py
    (touche 'q' pour quitter)
"""

import argparse
import os

import cv2
import mediapipe as mp

# --- Config ---------------------------------------------------------------

# Résolu par rapport à l'emplacement du script, pas au dossier d'exécution.
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
DEBOUNCE_FRAMES = 4  # nb de frames consécutives identiques avant de changer l'image affichée

GESTURE_IMAGES = {
    "poing": os.path.join(ASSETS_DIR, "poing.png"),
    "main_ouverte": os.path.join(ASSETS_DIR, "main_ouverte.png"),
    "peace": os.path.join(ASSETS_DIR, "peace.png"),
    "pouce": os.path.join(ASSETS_DIR, "pouce.png"),
}

# Landmarks MediaPipe : indices des bouts de doigts et des articulations
# de référence (PIP) pour savoir si un doigt est "tendu" ou "replié".
FINGER_TIPS = [4, 8, 12, 16, 20]   # pouce, index, majeur, annulaire, auriculaire
FINGER_PIPS = [3, 6, 10, 14, 18]

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils


def fingers_up(landmarks, handedness_label):
    """Retourne une liste de 5 booléens : doigt tendu ou non (pouce inclus)."""
    up = []

    # Pouce : comparaison horizontale (dépend de la main gauche/droite)
    if handedness_label == "Right":
        up.append(landmarks[4].x < landmarks[3].x)
    else:
        up.append(landmarks[4].x > landmarks[3].x)

    # Les 4 autres doigts : tendu si le bout est au-dessus de l'articulation PIP
    for tip, pip in zip(FINGER_TIPS[1:], FINGER_PIPS[1:]):
        up.append(landmarks[tip].y < landmarks[pip].y)

    return up  # [pouce, index, majeur, annulaire, auriculaire]


def classify_gesture(up: list[bool]) -> str | None:
    """Reconnaît un geste à partir de l'état des 5 doigts. None si ambigu."""
    thumb, index, middle, ring, pinky = up

    if not any(up):
        return "poing"
    if all(up):
        return "main_ouverte"
    if index and middle and not ring and not pinky and not thumb:
        return "peace"
    if thumb and not index and not middle and not ring and not pinky:
        return "pouce"
    return None


def main(camera_index: int = 0):
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print(f"Impossible d'ouvrir la webcam (index {camera_index}).")
        return

    # Précharge les images en mémoire
    overlays = {}
    for name, path in GESTURE_IMAGES.items():
        img = cv2.imread(path)
        if img is not None:
            overlays[name] = img
        else:
            print(f"Avertissement : image introuvable pour '{name}' ({path})")

    with mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.6,
    ) as hands:

        current_gesture = None
        pending_gesture = None
        pending_count = 0

        while True:
            ok, frame = cap.read()
            if not ok:
                break

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = hands.process(rgb)

            gesture = None
            if result.multi_hand_landmarks and result.multi_handedness:
                hand_landmarks = result.multi_hand_landmarks[0]
                label = result.multi_handedness[0].classification[0].label
                up = fingers_up(hand_landmarks.landmark, label)
                gesture = classify_gesture(up)
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Debounce : n'affiche un nouveau geste que s'il est stable
            # sur plusieurs frames consécutives, pour éviter le flicker.
            if gesture and gesture == pending_gesture:
                pending_count += 1
            else:
                pending_gesture = gesture
                pending_count = 1 if gesture else 0

            if gesture and pending_count >= DEBOUNCE_FRAMES:
                current_gesture = gesture

            cv2.putText(
                frame,
                current_gesture or "...",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2,
            )

            cv2.imshow("Camera", frame)

            if current_gesture and current_gesture in overlays:
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
    args = parser.parse_args()
    main(camera_index=args.camera)
