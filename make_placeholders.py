# -*- coding: utf-8 -*-
"""Generate placeholder product photos into src/assets/img/product/.

These exist only so the site renders without broken images. To publish real
photos, overwrite the files with your own JPGs using the SAME file names:

    src/assets/img/product/hair-dryer-01.jpg          (main photo, used in cards)
    src/assets/img/product/hair-dryer-02.jpg          (detail thumbnail 2)
    src/assets/img/product/hair-dryer-03.jpg          (detail thumbnail 3)
    src/assets/img/product/hair-dryer-04.jpg          (detail thumbnail 4)

Same pattern for curling-iron, hair-straightener, straightening-brush.

No code change is needed - just run build.py again afterwards so the new
files are copied into dist/. Recommended size: at least 1000x750, square
crop is fine, JPG or PNG (if you use PNG, rename the reference in build.py).

Usage:  python make_placeholders.py
"""
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "src", "assets", "img", "product")

W, H = 1000, 750
PER_PRODUCT = 4

PRODUCTS = [
    ("hair-dryer", "High-Speed Ionic Hair Dryer", "LV-HD01"),
    ("curling-iron", "Professional Curling Iron", "LV-CI02"),
    ("hair-straightener", "Titanium Hair Straightener", "LV-ST03"),
    ("straightening-brush", "Heated Straightening Brush", "LV-SB04"),
]


def load_font(size):
    for path in (r"C:\Windows\Fonts\segoeui.ttf", r"C:\Windows\Fonts\arial.ttf"):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def dashed_rect(draw, box, color, dash=14, gap=10, width=3):
    x0, y0, x1, y1 = box
    for y in (y0, y1):
        x = x0
        while x < x1:
            draw.line([x, y, min(x + dash, x1), y], fill=color, width=width)
            x += dash + gap
    for x in (x0, x1):
        y = y0
        while y < y1:
            draw.line([x, y, x, min(y + dash, y1)], fill=color, width=width)
            y += dash + gap


def centered(draw, y, text, fnt, fill):
    bbox = draw.textbbox((0, 0), text, font=fnt)
    draw.text(((W - (bbox[2] - bbox[0])) / 2, y), text, font=fnt, fill=fill)


def make(path, title, model, idx):
    img = Image.new("RGB", (W, H), (244, 246, 248))
    d = ImageDraw.Draw(img)

    dashed_rect(d, (40, 40, W - 40, H - 40), (205, 213, 223))

    # Simple camera glyph so the slot reads as "photo goes here".
    cx, cy, s = W / 2, H / 2 - 70, 74
    d.rounded_rectangle([cx - s, cy - s * 0.62, cx + s, cy + s * 0.62],
                        radius=18, outline=(176, 188, 203), width=6)
    d.ellipse([cx - 26, cy - 26, cx + 26, cy + 26],
              outline=(176, 188, 203), width=6)
    d.rounded_rectangle([cx + s * 0.45, cy - s * 0.5, cx + s * 0.78, cy - s * 0.24],
                        radius=6, outline=(176, 188, 203), width=5)

    f_title = load_font(40)
    f_meta = load_font(26)
    f_note = load_font(22)

    centered(d, H / 2 + 30, title, f_title, (91, 107, 124))
    centered(d, H / 2 + 92, "%s  \u00b7  photo %d of %d" % (model, idx, PER_PRODUCT),
             f_meta, (140, 155, 172))
    centered(d, H - 120, "PLACEHOLDER \u2014 replace this file with a real photo",
             f_note, (176, 188, 203))

    img.save(path, "JPEG", quality=82, optimize=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    count = 0
    for slug, title, model in PRODUCTS:
        for i in range(1, PER_PRODUCT + 1):
            path = os.path.join(OUT, "%s-%02d.jpg" % (slug, i))
            make(path, title, model, i)
            count += 1
    print("Generated %d placeholder photos -> %s" % (count, OUT))
    for slug, _t, _m in PRODUCTS:
        print("  %s-01..%02d.jpg" % (slug, PER_PRODUCT))


if __name__ == "__main__":
    main()
