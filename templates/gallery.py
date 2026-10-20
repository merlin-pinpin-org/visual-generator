#!/usr/bin/env python3
"""Template: gallery grid (N items, art + caption each).

Renders a titled grid of items — territory gallery, civilization
roster, season highlights. Items auto-wrap in fixed columns; each
cell draws its art and a caption plate (caption + optional sub line).

JSON schema::

    {
      "template": "gallery",
      "output": "examples/gallery.jpg",
      "sections": {
        "title": "DEMO GAME — Territories",
        "item_width": 400, "item_height": 500,
        "columns": 4, "gap": 24,
        "items": [
          {"art": "path/art.jpg", "caption": "Forêt Noire",
           "sub": "Offre la civilisation des Celtes"}
        ]
      }
    }
"""
from __future__ import annotations

import math

from PIL import Image, ImageDraw, ImageFont

DEFAULT_PALETTE = {
    "bg": (24, 20, 16), "band": (34, 48, 30), "gold": (92, 138, 78),
    "gold2": (66, 96, 58), "text_light": (224, 238, 210),
    "subtitle": (200, 216, 190), "title_txt": (218, 193, 121),
}

MARGIN = 40
TITLE_H = 90


def wrap(draw, text, font, maxw):
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


def render(data, fonts):
    sec = data["sections"]
    pal = resolve_palette(DEFAULT_PALETTE, data.get("palette"))
    iw, ih = sec.get("item_width", 440), sec.get("item_height", 560)
    cols, gap = sec.get("columns", 4), sec.get("gap", 26)
    items = sec["items"]
    rows = math.ceil(len(items) / cols)

    W = MARGIN * 2 + cols * iw + (cols - 1) * gap
    H = MARGIN * 2 + TITLE_H + rows * (ih + 150) + (rows - 1) * gap
    c = Image.new("RGB", (W, H), pal["bg"])
    d = ImageDraw.Draw(c)

    d.text((W // 2, MARGIN + 30), sec["title"], font=ImageFont.truetype(fonts["b"], 48),
           fill=pal["title_txt"], anchor="mm")

    cap_f = ImageFont.truetype(fonts["b"], 34)
    sub_f = ImageFont.truetype(fonts["r"], 26)
    for idx, item in enumerate(items):
        r, col = divmod(idx, cols)
        x = MARGIN + col * (iw + gap)
        y = MARGIN + TITLE_H + r * (ih + 150 + gap)
        art = Image.open(item["art"]).convert("RGB").resize((iw, ih))
        c.paste(art, (x, y))
        d.rectangle([x, y, x + iw - 1, y + ih - 1], outline=pal["gold2"], width=3)
        d.rectangle([x, y + ih, x + iw - 1, y + ih + 140], fill=pal["band"],
                    outline=pal["gold"], width=3)
        d.text((x + 20, y + ih + 34), item["caption"], font=cap_f,
               fill=pal["text_light"], anchor="lm")
        if item.get("sub"):
            lines = wrap(d, item["sub"], sub_f, iw - 40)[:3]
            sy = y + ih + 78
            for ln in lines:
                d.text((x + 20, sy), ln, font=sub_f, fill=pal["subtitle"], anchor="lm")
                sy += 32
    return c
