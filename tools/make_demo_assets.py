#!/usr/bin/env python3
"""Generate the demo art assets for the library examples.

All art is procedural (Pillow only): no text, no letters — the image
model never renders text, and neither does this script. Each asset is
a stand-in for a real game asset or an image-model illustration.
"""
from __future__ import annotations

import os
import random

from PIL import Image, ImageDraw, ImageFilter

OUT = "examples/assets"


def parchment(path, w=1400, h=2050):
    rng = random.Random(7)
    base = (216, 196, 156)
    img = Image.new("RGB", (w, h), base)
    d = ImageDraw.Draw(img)
    for _ in range(2600):
        x, y = rng.randrange(w), rng.randrange(h)
        shade = rng.randint(-26, 20)
        d.point((x, y), fill=tuple(max(0, min(255, c + shade)) for c in base))
    for _ in range(140):
        x, y = rng.randrange(w), rng.randrange(h)
        r = rng.randint(4, 26)
        c = (196 + rng.randint(-16, 14), 176 + rng.randint(-16, 14), 136 + rng.randint(-16, 14))
        d.ellipse([x - r, y - r, x + r, y + r], fill=c)
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w - 1, h - 1], outline=(120, 92, 52), width=14)
    d.rectangle([26, 26, w - 27, h - 27], outline=(150, 118, 70), width=4)
    img.save(path, quality=88)


def crest(path, seed, w=1024, h=1024):
    rng = random.Random(seed)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    hues = [(168, 60, 48), (58, 88, 148), (64, 118, 66), (150, 112, 44), (104, 62, 132)]
    c1, c2 = rng.sample(hues, 2)
    shield = [(w * 0.12, h * 0.08), (w * 0.88, h * 0.08), (w * 0.88, h * 0.62),
              (w * 0.5, h * 0.95), (w * 0.12, h * 0.62)]
    d.polygon(shield, fill=c1 + (255,), outline=(38, 28, 18, 255))
    d.polygon([(w * 0.12, h * 0.08), (w * 0.5, h * 0.08), (w * 0.5, h * 0.95),
               (w * 0.12, h * 0.62)], fill=c2 + (255,))
    for _ in range(5):
        x, y = rng.randrange(int(w * 0.2), int(w * 0.8)), rng.randrange(int(h * 0.12), int(h * 0.55))
        r = rng.randint(20, 60)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(235, 222, 190, 255),
                  outline=(38, 28, 18, 255), width=6)
    for _ in range(3):
        x1, y1 = rng.randrange(int(w * 0.15), int(w * 0.7)), rng.randrange(int(h * 0.1), int(h * 0.5))
        x2, y2 = x1 + rng.randint(60, 240), y1 + rng.randint(60, 240)
        d.line([x1, y1, x2, y2], fill=(235, 222, 190, 255), width=10)
    img.save(path, optimize=True)


def icon(path, seed, w=104):
    rng = random.Random(seed)
    img = Image.new("RGBA", (w, w), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = rng.choice([(168, 60, 48), (58, 88, 148), (64, 118, 66), (150, 112, 44)])
    d.ellipse([2, 2, w - 3, w - 3], fill=c + (255,), outline=(38, 28, 18, 255), width=3)
    for _ in range(4):
        x, y = rng.randrange(14, w - 14), rng.randrange(14, w - 14)
        r = rng.randint(6, 16)
        d.polygon([(x, y - r), (x + r, y), (x, y + r), (x - r, y)], fill=(235, 222, 190, 255))
    img.save(path, optimize=True)


def scene(path, seed, w=1200, h=675, sky=(96, 76, 56)):
    rng = random.Random(seed)
    img = Image.new("RGB", (w, h), sky)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w, h * 0.55], fill=(88, 70, 54))
    d.rectangle([0, int(h * 0.55), w, h], fill=(52, 44, 32))
    for i in range(6):
        x = int(w * (i + 0.5) / 6) + rng.randint(-40, 40)
        peak = rng.randint(int(h * 0.18), int(h * 0.45))
        d.polygon([(x - rng.randint(90, 160), h), (x, h - peak), (x + rng.randint(90, 160), h)],
                  fill=(70 + rng.randint(-10, 14), 58 + rng.randint(-8, 12), 44))
    for _ in range(28):
        x, y = rng.randrange(w), rng.randrange(int(h * 0.75))
        r = rng.randint(8, 30)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(44, 36, 26))
    img = img.filter(ImageFilter.GaussianBlur(1.2))
    img.save(path, quality=86)


def territory(path, seed, w=500, h=500):
    rng = random.Random(seed)
    img = Image.new("RGB", (w, h), (46, 58, 40))
    d = ImageDraw.Draw(img)
    c = rng.choice([(64, 92, 58), (110, 96, 54), (70, 80, 100), (120, 96, 66)])
    d.rectangle([0, 0, w, h], fill=c)
    for _ in range(9):
        x, y = rng.randrange(w), rng.randrange(h)
        rx, ry = rng.randint(30, 120), rng.randint(20, 80)
        shade = tuple(max(0, min(255, v + rng.randint(-26, 26))) for v in c)
        d.ellipse([x - rx, y - ry, x + rx, y + ry], fill=shade)
    d.rectangle([0, int(h * 0.66), w, h], fill=tuple(max(0, v - 18) for v in c))
    img = img.filter(ImageFilter.GaussianBlur(0.8))
    img.save(path, quality=86)


def card_art(path, seed, w=800, h=640):
    rng = random.Random(seed)
    img = Image.new("RGB", (w, h), (34, 28, 20))
    d = ImageDraw.Draw(img)
    for i in range(14):
        x, y = rng.randrange(w), rng.randrange(h)
        r = rng.randint(24, 90)
        c = rng.choice([(70, 56, 36), (52, 64, 44), (86, 66, 40)])
        d.ellipse([x - r, y - r, x + r, y + r], fill=c)
    for _ in range(4):
        x1, y1 = rng.randrange(w), rng.randrange(h)
        d.line([x1, y1, x1 + rng.randint(-160, 160), y1 + rng.randint(-120, 120)],
               fill=(150, 120, 70), width=5)
    img = img.filter(ImageFilter.GaussianBlur(1.5))
    img.save(path, quality=86)



def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    parchment(f"{OUT}/parchment.jpg")
    crest(f"{OUT}/crest_lion.png", 11)
    crest(f"{OUT}/crest_stag.png", 29)
    icon(f"{OUT}/civ_red.png", 3)
    icon(f"{OUT}/civ_blue.png", 5)
    icon(f"{OUT}/civ_green.png", 8)
    scene(f"{OUT}/battle.jpg", 13)
    card_art(f"{OUT}/card_art_ambush.jpg", 17)
    for i, name in enumerate(["northern-pass", "twin-lakes", "black-forest",
                              "golden-coast", "iron-hills", "sun-valley",
                              "mist-marsh", "old-crossroad"], start=21):
        territory(f"{OUT}/terr_{name}.jpg", i)
    print("demo assets written to", OUT)


if __name__ == "__main__":
    main()
