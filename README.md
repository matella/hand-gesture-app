# hand-gesture-image

Petite app Python qui capture le flux webcam, détecte la main via le modèle
pré-entraîné [MediaPipe GestureRecognizer](https://ai.google.dev/edge/mediapipe/solutions/vision/gesture_recognizer),
reconnaît un geste simple (poing, main ouverte, peace, pouce) et affiche une
image correspondante dans une fenêtre séparée — idéal à capturer dans OBS via
une *Window Capture* sur la fenêtre "Image".

Inspiré d'un reel Instagram montrant ce type d'effet en temps réel.

## Installation

```bash
pip install -r requirements.txt
```

Testé avec Python 3.13. Au premier lancement, le script télécharge
automatiquement le modèle MediaPipe GestureRecognizer (~8 Mo) dans `models/`.

## Utilisation

```bash
python gesture_display.py
```

- Fenêtre **Camera** : flux webcam avec les points de la main dessinés.
- Fenêtre **Image** : image correspondant au geste détecté (à capturer dans OBS).
- Touche `q` pour quitter.

Si les gestes doivent être trop "parfaits" pour être reconnus, baisse le seuil
de confiance (défaut 0.5) :

```bash
python gesture_display.py --gesture-threshold 0.3
```

À l'inverse, augmente-le si l'appli confond deux gestes proches trop souvent.

## Personnaliser les images

Chaque geste pointe vers un fichier dans `assets/`, listé dans `GESTURE_IMAGES`
en haut de [`gesture_display.py`](gesture_display.py) — modifie ce dict pour
changer les fichiers utilisés (n'importe quel format lisible par
`cv2.imread` : `.png`, `.jpg`, `.gif`, ... ; pour un `.gif`, seule la première
image est affichée, pas l'animation).

Tu peux régénérer les placeholders avec :

```bash
python generate_assets.py
```

## Gestes reconnus

Classés par le modèle pré-entraîné MediaPipe GestureRecognizer (catégorie
correspondante entre parenthèses) :

| Geste | Description |
|---|---|
| `poing` | Poing fermé (`Closed_Fist`) |
| `main_ouverte` | Main ouverte, doigts tendus (`Open_Palm`) |
| `peace` | Signe de la victoire (`Victory`) |
| `pouce` | Pouce levé (`Thumb_Up`) |
| `shush` | Poing avec index levé, geste "chut" (`Pointing_Up`) |
| `neutre` | Aucune main détectée, ou geste non reconnu |

`Thumb_Down` (pouce vers le bas) n'est pas mappé : visuellement trop proche de
`Closed_Fist` selon la position du pouce (le modèle confond parfois les
deux), et il n'existe pas de catégorie "shaka" dédiée. Un poing mal reconnu
comme `Thumb_Down` retombe donc sur `neutre` plutôt que d'afficher une image
qui ne correspond pas au geste fait. `assets/swag.gif` (signe shaka) reste
disponible mais n'est câblé à rien.

## Développement

Ce projet suit un workflow **spec-driven, test-first** : voir
[`specs/README.md`](specs/README.md) pour le process complet, et
[`specs/`](specs/) pour les specs de chaque fonctionnalité.

```bash
pip install -r requirements-dev.txt
pytest
```

## Licence

MIT
