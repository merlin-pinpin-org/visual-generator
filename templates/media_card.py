#!/usr/bin/env python3
"""Template: media card — art-backed card with an image strip.

One full-bleed **background art** (fixed, darkened), a title band over
it, a calculated strip of 1–4 inserted images, tag chips, a facts
line, and the description on a plate. The strip tiles are computed
from the canvas width — each image is center-cropped into its window.

JSON schema::

    {
      "template": "media_card",
      "output": "examples/media_card_map.jpg",
      "canvas": {"width": 1000, "height": 750},
      "palette": {"accent": "#5c8a4e"},
      "art": "path/to/background_art.jpg",      # required: full-bleed backdrop
      "sections": {
        "title": "Arabie",
        "subtitle": "Map — Ouverte · 1v1",
        "tags": ["Ouverte", "1v1"],
        "images": ["path/img1.jpg", "path/img2.jpg"],   # strip, max 4
        "facts": [["Taille", "Moyenne"]],
        "description": "Synthesized description…",
        "footer": "map:aoe2:arabia"
      }
    }

Design rules (learned the hard way — keep them):

- The background art gets a 58% veil: the strip and plates must stay
  readable over it.
- Strip windows: equal fractions of the inner width — computed from
  the image count, never hand-placed.
- The description plate clips visibly: the data must be synthesized.
"""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

DEFAULT_PALETTE = {
    "veil": (10, 12, 9), "plate": (18, 24, 16), "plate_edge": (92, 138, 78),
    "accent": (92, 138, 78), "text_light": (226, 240, 212),
    "subtitle": (200, 216, 190), "chip_bg": (24, 32, 20),
    "chip_txt": (214, 234, 196), "label": (150, 196, 130),
    "ink": (234, 240, 220), "footer_txt": (160, 176, 140),
}

W, H = 1000, 750
VEIL = 0.58
STRIP_H = 250


def _wrap(draw, text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= maxw:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _crop(img, w, h):
    scale = max(w / img.width, h / img.height)
    big = img.resize((int(img.width * scale), int(img.height * scale)))
    x, y = (big.width - w) // 2, (big.height - h) // 2
    return big.crop((x, y, x + w, y + h))


def render(data, fonts):
    sec = data["sections"]
    pal = resolve_palette(DEFAULT_PALETTE, data.get("palette"))

    # --- background art (fixed) ---
    art = Image.open(data["art"]).convert("RGB").resize((W, H))
    veil = Image.new("RGB", (W, H), pal["veil"])
    c = Image.blend(art, veil, VEIL)
    d = ImageDraw.Draw(c)
    d.rectangle([0, 0, W - 1, H - 1], outline=pal["accent"], width=6)

    # --- header band over the art ---
    d.rectangle([0, 0, W - 1, 104], fill=(12, 16, 11))
    d.line([0, 104, W - 1, 104], fill=pal["accent"], width=3)
    d.text((44, 44), sec["title"], font=ImageFont.truetype(fonts["b"], 44),
           fill=pal["text_light"], anchor="lm")
    d.text((W - 44, 74), sec.get("subtitle", ""), font=ImageFont.truetype(fonts["i"], 22),
           fill=pal["subtitle"], anchor="rm")

    # --- image strip (calculated windows) ---
    images = sec.get("images", [])[:4]
    y0 = 128
    if images:
        n = len(images)
        gap = 10
        iw = (W - 88 - (n - 1) * gap) // n
        x = 44
        for p in images:
            img = Image.open(p).convert("RGB")
            c.paste(_crop(img, iw, STRIP_H), (x, y0))
            d.rectangle([x, y0, x + iw - 1, y0 + STRIP_H - 1],
                        outline=pal["plate_edge"], width=3)
            x += iw + gap
        y0 += STRIP_H + 18

    # --- tags ---
    tags = sec.get("tags", [])[:5]
    if tags:
        cf = ImageFont.truetype(fonts["r"], 20)
        x = 44
        for tag in tags:
            tw = int(d.textlength(tag, font=cf)) + 24
            d.rounded_rectangle([x, y0, x + tw, y0 + 34], radius=17,
                                fill=pal["chip_bg"], outline=pal["accent"], width=2)
            d.text((x + 12, y0 + 17), tag, font=cf, fill=pal["chip_txt"], anchor="lm")
            x += tw + 8
        y0 += 46

    # --- facts line on a plate ---
    facts = sec.get("facts", [])[:4]
    if facts:
        ff = ImageFont.truetype(fonts["r"], 21)
        width = int(sum(d.textlength(f"{l} : {v}", font=ff) + 30 for l, v in facts)) + 24
        d.rounded_rectangle([44, y0, 44 + width, y0 + 40], radius=8,
                            fill=pal["plate"], outline=(60, 76, 52), width=2)
        x = 56
        for label, value in facts:
            d.text((x, y0 + 20), f"{label} :", font=ff, fill=pal["label"], anchor="lm")
            x += int(d.textlength(f"{label} :", font=ff))
            d.text((x + 6, y0 + 20), str(value), font=ff, fill=pal["ink"], anchor="lm")
            x += int(d.textlength(str(value), font=ff)) + 30
        y0 += 52

    # --- description plate (clips visibly) ---
    desc = sec.get("description", "")
    if desc:
        box_bottom = H - 66
        d.rounded_rectangle([44, y0, W - 45, box_bottom], radius=12,
                            fill=pal["plate"], outline=pal["plate_edge"], width=2)
        df = ImageFont.truetype(fonts["r"], 22)
        lines = _wrap(d, desc, df, W - 132)[: max(1, (box_bottom - y0 - 24) // 30)]
        y = y0 + 16
        for ln in lines:
            d.text((68, y), ln, font=df, fill=pal["ink"])
            y += 30

    d.text((W - 44, H - 24), sec.get("footer", ""),
           font=ImageFont.truetype(fonts["r"], 19), fill=pal["footer_txt"], anchor="rm")
    return c
