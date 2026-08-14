# hand-gesture-image

Petite app Python qui capture le flux webcam, détecte la position de la main
via [MediaPipe Hands](https://developers.google.com/mediapipe), reconnaît un
geste simple (poing, main ouverte, peace, pouce) et affiche une image
correspondante dans une fenêtre séparée — idéal à capturer dans OBS via une
*Window Capture* sur la fenêtre "Image".

Inspiré d'un reel Instagram montrant ce type d'effet en temps réel.

## Installation

```bash
pip install -r requirements.txt
```

## Utilisation

```bash
python gesture_display.py
```

- Fenêtre **Camera** : flux webcam avec les points de la main dessinés.
- Fenêtre **Image** : image correspondant au geste détecté (à capturer dans OBS).
- Touche `q` pour quitter.

## Personnaliser les images

Remplace les fichiers dans `assets/` (`poing.png`, `main_ouverte.png`,
`peace.png`, `pouce.png`) par tes propres visuels — même nom, même dossier.

Tu peux régénérer les placeholders avec :

```bash
python generate_assets.py
```

## Gestes reconnus

| Geste | Description |
|---|---|
| `poing` | Tous les doigts repliés |
| `main_ouverte` | Tous les doigts tendus |
| `peace` | Index + majeur tendus uniquement |
| `pouce` | Pouce tendu uniquement |

## Licence

MIT
