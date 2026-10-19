#!/usr/bin/env python3
"""Template: media card — several images, tags, synthesized description.

One visual that replaces a media-heavy post: map sheet, location card,
highlight reel. A gallery strip (2–4 images) across the top, a title
band, tag chips, and a description block that wraps over several
lines — the "grosse description à synthétiser" case: the JSON carries
the full text, the card wraps it and clips it at the box, so the
author synthesizes before shipping (fail-closed spirit: too much
text is cut visibly).

JSON schema::

    {
      "template": "media_card",
      "output": "examples/map_card.jpg",
      "canvas": {"width": 1000, "height": 750},         # optional
      "palette": {"accent": "#5c8a4e"},                 # optional
      "art": "path/to/backdrop.jpg",                    # optional dim backdrop
      "sections": {
        "title": "Arabie",
        "subtitle": "Map — Open",
        "tags": ["1v1", "Élévations", "Chameaux"],
        "images": ["path/img1.jpg", "path/img2.jpg", "path/img3.jpg"],
        "description": "Carte ouverte au centre, collines escarpées…",
        "facts": [["Taille", "Moyenne"], ["Type", "Arabe"]],
        "footer": "map:aoe2:arabia · Source : liquipedia"
      }
    }
"""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

DEFAULT_PALETTE = {
    "bg": (20, 26, 18), "panel": (28, 38, 24), "accent": (92, 138, 78),
    "accent2": (66, 96, 58), "text_light": (224, 238, 210),
    "subtitle": (200, 216, 190), "chip_bg": (34, 48, 30),
    "chip_txt": (218, 238, 200), "label": (140, 190, 120),
    "ink": (238, 232, 208), "footer_txt": (150, 160, 130),
    "line": (70, 90, 60), "box": (30, 40, 26),
}

W, H = 1000, 750
STRIP_H = 300


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
    c = Image.new("RGB", (W, H), pal["bg"])
    d = ImageDraw.Draw(c)

    art_path = data.get("art")
    if art_path:
        art = Image.open(art_path).convert("RGB").resize((W, H))
        c.paste(Image.blend(c, art, 0.25), (0, 0))
        d = ImageDraw.Draw(c)

    d.rectangle([0, 0, W - 1, H - 1], outline=pal["accent"], width=6)

    # header
    d.rectangle([0, 0, W - 1, 96], fill=pal["panel"])
    d.line([0, 96, W - 1, 96], fill=pal["accent"], width=3)
    d.text((40, 34), sec["title"], font=ImageFont.truetype(fonts["b"], 42),
           fill=pal["text_light"], anchor="lm")
    d.text((W - 40, 66), sec.get("subtitle", ""), font=ImageFont.truetype(fonts["i"], 22),
           fill=pal["subtitle"], anchor="rm")

    # image strip
    images = sec.get("images", [])
    if images:
        n = max(1, min(4, len(images)))
        gap = 12
        iw = (W - 80 - (n - 1) * gap) // n
        x = 40
        for p in images[:4]:
            img = Image.open(p).convert("RGB")
            c.paste(_crop(img, iw, STRIP_H), (x, 116))
            d.rectangle([x, 116, x + iw - 1, 116 + STRIP_H - 1],
                        outline=pal["accent2"], width=3)
            x += iw + gap

    # tags
    tags = sec.get("tags", [])
    y0 = 116 + (STRIP_H + 20 if images else 20)
    if tags:
        cf = ImageFont.truetype(fonts["r"], 21)
        x = 40
        for tag in tags[:6]:
            tw = int(d.textlength(tag, font=cf)) + 26
            d.rounded_rectangle([x, y0, x + tw, y0 + 36], radius=18,
                                fill=pal["chip_bg"], outline=pal["accent2"], width=2)
            d.text((x + 13, y0 + 18), tag, font=cf, fill=pal["chip_txt"], anchor="lm")
            x += tw + 10
        y0 += 48

    # facts line
    facts = sec.get("facts", [])
    if facts:
        ff = ImageFont.truetype(fonts["r"], 22)
        x = 40
        for label, value in facts[:5]:
            d.text((x, y0), f"{label} :", font=ff, fill=pal["label"], anchor="lm")
            x += int(d.textlength(f"{label} : ", font=ff))
            d.text((x, y0), str(value), font=ff, fill=pal["ink"], anchor="lm")
            x += int(d.textlength(str(value), font=ff)) + 28
        y0 += 40

    # description box
    desc = sec.get("description", "")
    if desc:
        box_top = y0
        box_bottom = H - 70
        d.rounded_rectangle([40, box_top, W - 41, box_bottom], radius=12,
                            fill=pal["box"], outline=pal["accent2"], width=2)
        df = ImageFont.truetype(fonts["r"], 23)
        lines = _wrap(d, desc, df, W - 80 - 56)[: max(1, (box_bottom - box_top - 28) // 30)]
        y = box_top + 18
        for ln in lines:
            d.text((68, y), ln, font=df, fill=pal["ink"])
            y += 30

    d.text((W - 40, H - 28), sec.get("footer", ""), font=ImageFont.truetype(fonts["r"], 19),
           fill=pal["footer_txt"], anchor="rm")
    return c
