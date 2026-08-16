"""Génère des images placeholder pour chaque geste (à remplacer par tes propres images)."""
import os

from PIL import Image, ImageDraw, ImageFont

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

GESTURES = {
    "poing": "#E63946",
    "main_ouverte": "#2A9D8F",
    "peace": "#457B9D",
    "pouce": "#F4A261",
    "surprise": "#9D4EDD",
    "smile": "#FFD166",
    "wink": "#06D6A0",
    "eyebrows": "#EF476F",
    "neutre": "#6C757D",
}

for name, color in GESTURES.items():
    img = Image.new("RGB", (640, 480), color)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
    except Exception:
        font = ImageFont.load_default()
    text = name.replace("_", " ").upper()
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((640 - w) / 2, (480 - h) / 2), text, fill="white", font=font)
    out_path = os.path.join(ASSETS_DIR, f"{name}.png")
    img.save(out_path)
    print(f"{out_path} généré")
