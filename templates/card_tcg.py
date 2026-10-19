#!/usr/bin/env python3
"""Template: TCG card (portrait, art window, text sections).

Fixed template anatomy (fractions of the canvas — never moved by the
art or the data)::

    0.00–0.10  outer gold frame + name banner
    0.10–0.55  art window (full-bleed art, center-cropped to fit)
    0.55–0.58  type line
    0.58–0.86  rule box (fixed; text vertically centered inside)
    0.86–0.94  extra box (only when extra_label is set)
    0.94–1.00  footer (index + signature)

The art never reserves blank zones: it is center-cropped into the
fixed window. Text zones belong to the template alone.

JSON schema::

    {
      "template": "card_tcg",
      "output": "examples/card.jpg",
      "palette": {"gold": "#b08d4a"},            # optional overrides
      "canvas": {"width": 744, "height": 1032},   # optional
      "sections": {
        "name": "Embuscade",
        "cost": 2,                    # int: drawn as N gear icons (Magic-style)
        "art": "path/to/art.jpg",           # full-bleed art, no text
        "type_line": "Action spéciale — Technologie",
        "rule": "Sentence one.\nSentence two.",   # \n = paragraph break
        "extra_label": "Condition liée :",  # optional bottom box
        "extra_value": "Celtes",
        "footer_left": "1/10",
        "footer_right": "Demo Game"
      }
    }
"""
from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

DEFAULT_PALETTE = {
    "bg": (40, 32, 22), "band": (52, 40, 24), "gold": (176, 141, 74),
    "gold2": (120, 96, 52), "text_light": (238, 220, 168),
    "subtitle": (205, 180, 130), "box": (238, 226, 196),
    "ink": (40, 30, 16), "badge": (176, 44, 32), "badge_ring": (218, 193, 121),
    "badge_txt": (255, 240, 210), "footer": (52, 40, 24),
    "footer_txt": (205, 180, 130),
}

F_NAME = 0.10
F_ART = 0.55
F_TYPE = 0.58
F_RULE = 0.86
F_EXTRA = 0.94
MARGIN_X = 36


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


def crop_to(art, w, h):
    """Center-crop art to the w:h window (no stretching, no empty zones)."""
    aw, ah = art.size
    scale = max(w / aw, h / ah)
    nw, nh = int(aw * scale), int(ah * scale)
    big = art.resize((nw, nh))
    x, y = (nw - w) // 2, (nh - h) // 2
    return big.crop((x, y, x + w, y + h))


def draw_gear(d, cx, cy, r):
    """Vector gear icon (tech currency): gold disc, dark teeth + hub."""
    import math
    teeth = 8
    pts = []
    for i in range(teeth * 2):
        ang = i * math.pi / teeth
        rad = r if i % 2 == 0 else r * 1.35
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    d.polygon(pts, fill=(60, 50, 30))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(218, 193, 121), outline=(120, 96, 52), width=2)
    d.ellipse([cx - r * 0.38, cy - r * 0.38, cx + r * 0.38, cy + r * 0.38],
              fill=(52, 40, 24))


def render(data, fonts):
    sec = data["sections"]
    pal = resolve_palette(DEFAULT_PALETTE, data.get("palette"))
    cw = data.get("canvas", {}).get("width", 744)
    ch = data.get("canvas", {}).get("height", 1032)
    c = Image.new("RGB", (cw, ch), pal["bg"])
    d = ImageDraw.Draw(c)

    name_b = int(ch * F_NAME)
    art_b = int(ch * F_ART)
    type_b = int(ch * F_TYPE)
    rule_b = int(ch * F_RULE)
    extra_b = int(ch * F_EXTRA)

    d.rectangle([0, 0, cw - 1, ch - 1], outline=pal["gold"], width=10)
    d.rectangle([16, 16, cw - 17, ch - 17], outline=pal["gold2"], width=3)
    d.rectangle([26, 26, cw - 27, name_b], fill=pal["band"], outline=pal["gold"], width=3)
    nf = ImageFont.truetype(fonts["b"], 48 if len(sec["name"]) <= 12 else 40)
    d.text((60, (26 + name_b) // 2), sec["name"], font=nf, fill=pal["text_light"], anchor="lm")

    cost = sec.get("cost", 0)
    cy = (26 + name_b) // 2
    if isinstance(cost, str) and cost:
        r = 40
        cx = cw - 76
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=pal["badge"],
                  outline=pal["badge_ring"], width=4)
        cf = ImageFont.truetype(fonts["b"], 48 if len(cost) <= 2 else 30)
        d.text((cx, cy), cost, font=cf, fill=pal["badge_txt"], anchor="mm")
    else:
        try:
            cost = int(cost)
        except (TypeError, ValueError):
            cost = 0
        if cost > 0:
            gs = 34
            x0 = cw - 60 - cost * (gs + 6)
            for k in range(cost):
                draw_gear(d, x0 + k * (gs + 6) + gs // 2, cy, gs // 2)

    art = Image.open(sec["art"]).convert("RGB")
    win_w = cw - 88
    win_h = art_b - name_b - 18
    c.paste(crop_to(art, win_w, win_h), (44, name_b + 4))
    d.rectangle([44, name_b + 4, 44 + win_w - 1, name_b + 4 + win_h - 1],
                outline=pal["gold2"], width=3)

    d.text((cw // 2, (art_b + type_b) // 2 + 2), sec["type_line"],
           font=ImageFont.truetype(fonts["i"], 28), fill=pal["subtitle"], anchor="mm")

    has_extra = bool(sec.get("extra_label"))
    r_bottom = extra_b if has_extra else rule_b
    r_top = type_b + 6
    d.rounded_rectangle([MARGIN_X, r_top, cw - MARGIN_X - 1, r_bottom], radius=14,
                        fill=pal["box"], outline=pal["gold2"], width=3)
    rule = sec["rule"]
    rf = ImageFont.truetype(fonts["r"],
                            30 if len(rule) <= 120 else (26 if rule.count("\n") >= 3 else 27))
    line_h = rf.size + 14
    paragraphs = [wrap(d, p, rf, cw - 2 * MARGIN_X - 84) or [""] for p in rule.split("\n")]
    total_h = sum(len(pl) * line_h for pl in paragraphs) + (len(paragraphs) - 1) * 8
    y = (r_top + r_bottom) // 2 - total_h // 2
    for pl in paragraphs:
        for ln in pl:
            d.text((60, y), ln, font=rf, fill=pal["ink"])
            y += line_h
        y += 8

    if has_extra:
        d.rounded_rectangle([MARGIN_X, r_bottom + 12, cw - MARGIN_X - 1, extra_b], radius=14,
                            fill=pal["band"], outline=pal["gold"], width=3)
        d.text((cw // 2, (r_bottom + 12 + extra_b) // 2 - 16), sec["extra_label"],
               font=ImageFont.truetype(fonts["r"], 26), fill=pal["subtitle"], anchor="mm")
        d.text((cw // 2, (r_bottom + 12 + extra_b) // 2 + 18), sec["extra_value"],
               font=ImageFont.truetype(fonts["b"], 32), fill=pal["text_light"], anchor="mm")

    foot_t = extra_b + 8
    d.rectangle([26, foot_t, cw - 27, ch - 27], fill=pal["footer"], outline=pal["gold"], width=3)
    ff = ImageFont.truetype(fonts["r"], 24)
    d.text((48, (foot_t + ch - 27) // 2), sec.get("footer_left", ""), font=ff,
           fill=pal["footer_txt"], anchor="lm")
    d.text((cw - 48, (foot_t + ch - 27) // 2), sec.get("footer_right", ""), font=ff,
           fill=pal["footer_txt"], anchor="rm")
    return c
