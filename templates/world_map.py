#!/usr/bin/env python3
"""Template: annotated world map.

A real world-map art as the background (no text in the art), with the
game's territories pinned at geographic positions — many regions, one
label plate each, readable over the map.

JSON schema::

    {
      "template": "world_map",
      "output": "examples/world_map.jpg",
      "art": "path/to/world_map_art.jpg",
      "sections": {
        "title": "LE MONDE — SEMAINE 3",
        "footer": "Demo Game — Season II",
        "regions": [
          {"name": "Black Forest", "x": 210, "y": 330,
           "color": "#5c8a4e", "note": "Elks · Lion"}
        ]
      }
    }

``x``/``y`` are pixel coordinates on the 1600×1200 canvas (the title
band occupies the top 100 px). **Place regions on actual land** —
inspect the map art first (Americas west, Europe center-north,
Africa center-south, Asia east) and pin each territory where it
belongs geographically. Plates are parchment-tinted so labels stay
readable — and OCR-checkable — over busy map art.
"""
from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

DEFAULT_PALETTE = {
    "bg": (24, 20, 16), "plate": (240, 228, 200), "plate_edge": (120, 96, 52),
    "ink": (40, 30, 16), "title_txt": (240, 228, 200), "title_band": (52, 40, 24),
    "title_edge": (176, 141, 74), "subtitle": (205, 180, 130),
}

W, H = 1600, 1200


def render(data, fonts):
    sec = data["sections"]
    pal = resolve_palette(DEFAULT_PALETTE, data.get("palette"))
    c = Image.new("RGB", (W, H), pal["bg"])
    d = ImageDraw.Draw(c)

    art = Image.open(data["art"]).convert("RGB").resize((W, H - 100))
    c.paste(art, (0, 100))

    d.rectangle([0, 0, W - 1, H - 1], outline=pal["title_edge"], width=8)
    d.rectangle([0, 0, W - 1, 100], fill=pal["title_band"], outline=pal["title_edge"], width=3)
    d.text((W // 2, 50), sec["title"], font=ImageFont.truetype(fonts["b"], 52),
           fill=pal["title_txt"], anchor="mm")

    name_f = ImageFont.truetype(fonts["b"], 24)
    note_f = ImageFont.truetype(fonts["r"], 20)
    for region in sec["regions"]:
        x, y = region["x"], region["y"]
        r, g, b = tuple(int(region.get("color", "#b08d4a").lstrip("#")[i:i + 2], 16)
                        for i in (0, 2, 4))
        d.ellipse([x - 12, y - 12, x + 12, y + 12], fill=(r, g, b),
                  outline=pal["plate_edge"], width=3)

        label_w = max(d.textlength(region["name"], font=name_f),
                      d.textlength(region.get("note", ""), font=note_f)) + 28
        plate_h = 66 if region.get("note") else 42
        d.rounded_rectangle([x + 18, y - plate_h // 2, x + 18 + label_w, y + plate_h // 2],
                            radius=8, fill=pal["plate"], outline=pal["plate_edge"], width=2)
        d.text((x + 32, y - (11 if region.get("note") else 0)), region["name"],
               font=name_f, fill=pal["ink"], anchor="lm")
        if region.get("note"):
            d.text((x + 32, y + 18), region["note"], font=note_f,
                   fill=(90, 66, 34), anchor="lm")

    d.rectangle([0, H - 40, W - 1, H - 1], fill=pal["title_band"])
    d.text((W // 2, H - 20), sec.get("footer", ""), font=ImageFont.truetype(fonts["r"], 22),
           fill=pal["subtitle"], anchor="mm")
    return c
