#!/usr/bin/env python3
"""Template: info card — classic Discord profile/rank card pattern.

Layout (the established rank-card pattern, as popularized by canvacord
and every Discord profile card):

- a **banner** (the background art) across the top;
- the avatar/hero in a **circle** straddling the banner's bottom edge,
  with a thick ring in the card body color;
- the name large, right of the avatar, with the subtitle under it and
  tag chips below;
- the content sections as clean text directly on the dark body — no
  plates, no boxes;
- rounded corners (PNG with transparency).

JSON schema::

    {
      "template": "info_card",
      "output": "examples/info_card_france.png",
      "canvas": {"width": 1000, "height": 780},
      "palette": {"accent": "#b08d4a"},
      "art": "path/to/banner_art.jpg",        # required: top banner
      "hero": "path/to/avatar.png",           # circular, straddles the banner
      "sections": {
        "title": "Byzantins",
        "subtitle": "Civilisation défensive",
        "tags": ["Défensive"],
        "columns": [
          {"head": "Bonus de civilisation",
           "lines": [["•", "Bâtiments +10/20/30/40 % de PV"]]}
        ],
        "footer": "Source : aoe2techtree · faction:aoe2:Byzantines"
      }
    }

Design rules (the pattern's hard rules):

- The banner veil is light (0.35): the banner is decoration, the name
  must pop against it; the body carries the text.
- The avatar ring matches the body color exactly — the straddle only
  reads as a cut-out when the ring color is right.
- Content text sits directly on the body: heads in accent, lines in
  ink. Never box the text — the boxes were the v2 mistake.
"""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

DEFAULT_PALETTE = {
    "body": (23, 20, 16), "veil": (12, 10, 8), "ring": (23, 20, 16),
    "accent": (176, 141, 74), "title": (240, 232, 210),
    "subtitle": (205, 180, 130), "chip_bg": (38, 33, 25),
    "chip_txt": (218, 193, 121), "ink": (226, 218, 198),
    "bullet": (176, 141, 74), "footer_txt": (150, 132, 100),
}

W, H = 1000, 780
BANNER_H = 300
AVATAR = 230
RADIUS = 28
VEIL = 0.35
SS = 4  # supersampling for the circle masks


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


def _alpha(img):
    """Flatten any source onto the body color, preserving transparency."""
    if img.mode == "RGBA":
        return img
    rgba = img.convert("RGBA")
    return rgba


def _circle_mask(size):
    big = Image.new("L", (size * SS, size * SS), 0)
    d = ImageDraw.Draw(big)
    d.ellipse([0, 0, size * SS - 1, size * SS - 1], fill=255)
    return big.resize((size, size), Image.LANCZOS)


def render(data, fonts):
    sec = data["sections"]
    pal = resolve_palette(DEFAULT_PALETTE, data.get("palette"))

    card = Image.new("RGBA", (W, H), pal["body"] + (255,))
    d = ImageDraw.Draw(card)

    # --- banner ---
    art = Image.open(data["art"]).convert("RGB").resize((W, BANNER_H))
    veil = Image.new("RGB", (W, BANNER_H), pal["veil"])
    banner = Image.blend(art, veil, VEIL)
    card.paste(banner, (0, 0))
    # banner fade into the body (gradient strip)
    fade_h = 60
    for i in range(fade_h):
        alpha = int(255 * (i / fade_h))
        d.line([(0, BANNER_H - fade_h + i), (W - 1, BANNER_H - fade_h + i)],
               fill=pal["body"] + (alpha,))

    # --- avatar: circle straddling the banner edge, thick body-color ring ---
    hero = data.get("hero")
    if hero:
        src = _alpha(Image.open(hero))
        src.thumbnail((AVATAR * 4, AVATAR * 4))
        src = _crop(src.convert("RGB"), AVATAR, AVATAR)
        cx, cy = 60, BANNER_H - AVATAR // 2 - 10
        # ring
        ring_w = 10
        d.ellipse([cx - 4, cy - 4, cx + AVATAR + 3, cy + AVATAR + 3],
                  fill=pal["ring"])
        # avatar clipped in a circle (supersampled mask)
        mask = _circle_mask(AVATAR)
        card.paste(src, (cx, cy), mask)

    # --- name + subtitle (right of the avatar) ---
    nx = cx + AVATAR + 46 if hero else 60
    d.text((nx, BANNER_H - 42), sec["title"],
           font=ImageFont.truetype(fonts["b"], 56), fill=pal["title"], anchor="lm")
    d.text((nx + 2, BANNER_H + 8), sec.get("subtitle", ""),
           font=ImageFont.truetype(fonts["i"], 26), fill=pal["subtitle"], anchor="lm")

    # --- tag chips (under the name zone) ---
    tags = sec.get("tags", [])[:4]
    if tags:
        cf = ImageFont.truetype(fonts["r"], 21)
        x = nx
        y = BANNER_H + 38
        for tag in tags:
            tw = int(d.textlength(tag, font=cf)) + 28
            d.rounded_rectangle([x, y, x + tw, y + 34], radius=17,
                                fill=pal["chip_bg"], outline=pal["accent"], width=2)
            d.text((x + 14, y + 17), tag, font=cf, fill=pal["chip_txt"], anchor="lm")
            x += tw + 10

    # --- content sections: clean text directly on the body ---
    cols = sec.get("columns", [])
    top = BANNER_H + 92
    bottom = H - 56
    vf = ImageFont.truetype(fonts["r"], 21)
    hf = ImageFont.truetype(fonts["b"], 24)
    colw = (W - 120 - (len(cols) - 1) * 40) // max(1, len(cols))
    for i, col in enumerate(cols):
        x = 60 + i * (colw + 40)
        y = top
        d.text((x, y), col.get("head", ""), font=hf, fill=pal["accent"])
        y += 38
        for item in col.get("lines", []):
            label, value = item[0], item[1] if len(item) > 1 else ""
            prefix = "" if label == "•" else f"{label} : "
            lines = _wrap(d, prefix + str(value), vf, colw)[:6]
            for ln in lines:
                if ln.startswith("•"):
                    d.text((x + 2, y), "•", font=vf, fill=pal["bullet"])
                    d.text((x + 22, y), ln[1:].strip(), font=vf, fill=pal["ink"])
                else:
                    d.text((x, y), ln, font=vf, fill=pal["ink"])
                y += 29
            y += 6
        if i == 0:
            d.line([x, top - 18, x, min(y, bottom)], fill=(45, 40, 30), width=1)

    # --- footer ---
    d.text((W - 56, H - 34), sec.get("footer", ""),
           font=ImageFont.truetype(fonts["r"], 19), fill=pal["footer_txt"], anchor="rm")

    # --- rounded corners ---
    corner = _circle_mask(RADIUS * 2).resize((RADIUS * 2, RADIUS * 2))
    card_mask = Image.new("L", (W, H), 0)
    cm = ImageDraw.Draw(card_mask)
    cm.rounded_rectangle([0, 0, W - 1, H - 1], radius=RADIUS, fill=255)
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.paste(card, (0, 0), card_mask)
    return out
