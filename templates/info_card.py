#!/usr/bin/env python3
"""Template: info card — one image, dense structured info (profile card).

A single visual that replaces a long embed/view when a forum post (or
message) is essentially "a picture plus a lot of facts": civilization
sheet, player profile, unit stat block, guild roster entry. One
portrait/landscape art window, a title band, tag chips, and up to two
info columns of label/value lines. The image never shifts text zones.

JSON schema::

    {
      "template": "info_card",
      "output": "examples/civ_france.jpg",
      "canvas": {"width": 1000, "height": 700},          # optional
      "palette": {"accent": "#b08d4a"},                  # optional
      "art": "path/to/civ_art.jpg",                      # optional
      "sections": {
        "title": "Francs",
        "subtitle": "Civilisation — Infanterie",
        "tags": ["Infanterie", "Économie", "Château"],   # chips, max ~6
        "image": "path/to/portrait.jpg",                 # left window (optional with art)
        "image_caption": "Emblème",                      # small line under the image
        "columns": [
          {"head": "Forces",
           "lines": [["Bonus", "Moins cher villageois"],
                     ["Unité unique", "Throwing Axeman"]]},
          {"head": "Sièges",
           "lines": [["Technologie", "Beaudes"]]}
        ],
        "footer": "Source : aoe2techtree · faction:aoe2:Franks"
      }
    }

Either ``art`` (full-bleed dimmed backdrop) or nothing is used behind
the card; ``sections.image`` is the prominent window. Lines render as
``label : value`` with the label in accent color.
"""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

DEFAULT_PALETTE = {
    "bg": (26, 22, 18), "panel": (36, 30, 22), "accent": (176, 141, 74),
    "accent2": (120, 96, 52), "text_light": (238, 220, 168),
    "subtitle": (205, 180, 130), "chip_bg": (52, 40, 24),
    "chip_txt": (218, 193, 121), "label": (176, 141, 74),
    "ink": (238, 226, 196), "footer_txt": (150, 128, 92),
    "line": (90, 74, 48),
}

W, H = 1000, 700
IMG = 340


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


def render(data, fonts):
    sec = data["sections"]
    pal = resolve_palette(DEFAULT_PALETTE, data.get("palette"))
    c = Image.new("RGB", (W, H), pal["bg"])
    d = ImageDraw.Draw(c)

    art_path = data.get("art")
    if art_path:
        art = Image.open(art_path).convert("RGB").resize((W, H))
        c.paste(Image.blend(c, art, 0.30), (0, 0))
        d = ImageDraw.Draw(c)

    d.rectangle([0, 0, W - 1, H - 1], outline=pal["accent"], width=6)

    # header band
    d.rectangle([0, 0, W - 1, 110], fill=pal["panel"])
    d.line([0, 110, W - 1, 110], fill=pal["accent"], width=3)
    d.text((40, 42), sec["title"], font=ImageFont.truetype(fonts["b"], 46),
           fill=pal["text_light"], anchor="lm")
    d.text((W - 40, 78), sec.get("subtitle", ""), font=ImageFont.truetype(fonts["i"], 24),
           fill=pal["subtitle"], anchor="rm")

    # tags row
    tags = sec.get("tags", [])
    if tags:
        cf = ImageFont.truetype(fonts["r"], 22)
        x = 40
        for tag in tags[:6]:
            tw = int(d.textlength(tag, font=cf)) + 28
            d.rounded_rectangle([x, 132, x + tw, 172], radius=20,
                                fill=pal["chip_bg"], outline=pal["accent2"], width=2)
            d.text((x + 14, 152), tag, font=cf, fill=pal["chip_txt"], anchor="lm")
            x += tw + 12

    # image window (left)
    x_text = 40
    if sec.get("image"):
        img = Image.open(sec["image"]).convert("RGB")
        iw, ih = IMG, IMG
        scale = max(iw / img.width, ih / img.height)
        big = img.resize((int(img.width * scale), int(img.height * scale)))
        cx, cy = (big.width - iw) // 2, (big.height - ih) // 2
        c.paste(big.crop((cx, cy, cx + iw, cy + ih)), (40, 196))
        d.rectangle([40, 196, 40 + iw - 1, 196 + ih - 1], outline=pal["accent2"], width=3)
        if sec.get("image_caption"):
            d.text((40 + iw // 2, 196 + ih + 18), sec["image_caption"],
                   font=ImageFont.truetype(fonts["i"], 20), fill=pal["subtitle"], anchor="mm")
        x_text = 40 + IMG + 36

    # info columns
    cols = sec.get("columns", [])
    top = 196
    if cols:
        colw = (W - x_text - 40 - (len(cols) - 1) * 28) // len(cols)
        for i, col in enumerate(cols):
            x = x_text + i * (colw + 28)
            d.text((x, top), col.get("head", ""), font=ImageFont.truetype(fonts["b"], 28),
                   fill=pal["text_light"])
            d.line([x, top + 40, x + colw - 1, top + 40], fill=pal["line"], width=2)
            y = top + 58
            lf = ImageFont.truetype(fonts["r"], 22)
            vf = ImageFont.truetype(fonts["r"], 22)
            for label, value in col.get("lines", []):
                d.text((x, y), f"{label} :", font=lf, fill=pal["label"], anchor="lm")
                yy = y + 26
                for ln in _wrap(d, str(value), vf, colw)[:3]:
                    d.text((x, yy), ln, font=vf, fill=pal["ink"], anchor="lm")
                    yy += 28
                y = max(y + 26 + 28 * len(_wrap(d, str(value), vf, colw)[:1]),
                        yy) + 14
    d.text((W - 40, H - 28), sec.get("footer", ""), font=ImageFont.truetype(fonts["r"], 20),
           fill=pal["footer_txt"], anchor="rm")
    return c
