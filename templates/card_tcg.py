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
        "cost": 2,                    # int: drawn as N gold coins
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


def dominant_color(art):
    """Average color of the art, slightly saturated — the card's accent."""
    small = art.resize((32, 32))
    px = list(small.getdata())
    r = sum(p[0] for p in px) // len(px)
    g = sum(p[1] for p in px) // len(px)
    b = sum(p[2] for p in px) // len(px)
    return (r, g, b)


def tint_toward(color, accent, factor):
    """Blend a palette color toward the art accent (0 = untouched)."""
    return tuple(int(c + (a - c) * factor) for c, a in zip(color, accent))


def hue_shift(color, accent, factor):
    """Rotate a color's hue toward the accent's hue, keeping its own
    saturation and value (a gold frame becomes a cool steel blue frame
    under blue art, without going grey).
    """
    import colorsys

    r, g, b = (c / 255 for c in color)
    ar, ag, ab = (a / 255 for a in accent)
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    ah, as_, av = colorsys.rgb_to_hsv(ar, ag, ab)
    if as_ < 0.12:
        return color
    delta = (ah - h + 0.5) % 1.0 - 0.5
    h = (h + delta * factor) % 1.0
    s = min(1.0, s * (1.0 + 0.25 * factor))
    return tuple(round(c * 255) for c in colorsys.hsv_to_rgb(h, s, v))


def harmonize_palette(pal, accent):
    """Harmonize frame/banner colors with the art.

    Text-critical zones (rule box, ink, text_light) stay untouched:
    OCR contrast is never degraded. Only frame, banner and footer colors
    shift toward the art's hue; the JSON palette always wins over the
    automatic harmonization (explicit overrides are applied after).
    """
    for key, factor in (("gold", 0.45), ("gold2", 0.55), ("band", 0.50),
                        ("footer", 0.40), ("bg", 0.35)):
        pal[key] = hue_shift(pal[key], accent, factor)
    return pal


def art_with_fade(art, w, h, fade=18, frame_rgb=None):
    """Art window with a soft fade: edges dissolve into the frame color
    instead of a hard cut (the art melts into the card, not taped on).
    A mild inner vignette darkens the corners so the window gains depth
    without shifting any zone (the window keeps its exact size)."""
    import math

    base = crop_to(art, w, h).convert("RGB")
    frame_rgb = frame_rgb or DEFAULT_PALETTE["bg"]
    fade_px = max(1, fade)
    cx, cy = (w - 1) / 2.0, (h - 1) / 2.0
    mask = Image.new("L", (w, h))
    mask.putdata([
        round(255 * max(0, min(1, min(x, w - 1 - x, y, h - 1 - y) / fade_px))
              * (1.0 - 0.16 * min(1.0, math.hypot((x - cx) / cx, (y - cy) / cy)) ** 2))
        for y in range(h) for x in range(w)
    ])
    return Image.composite(base, Image.new("RGB", (w, h), frame_rgb), mask)


def draw_coin(d, cx, cy, r):
    """Vector gold coin (currency icon): shaded disc, rim, embossed star."""
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(196, 158, 80),
              outline=(110, 86, 42), width=2)
    d.ellipse([cx - r * 0.82, cy - r * 0.82, cx + r * 0.82, cy + r * 0.82],
              fill=(224, 190, 110), outline=(150, 118, 58), width=2)
    d.regular_polygon((cx, cy, r * 0.34), 5, rotation=-90, fill=(255, 228, 160))
    d.ellipse([cx - r * 0.18, cy - r * 0.18, cx - r * 0.02, cy - r * 0.02],
              fill=(255, 240, 200))


def hex_to_rgb(value: str):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def render(data, fonts):
    sec = data["sections"]
    pal = dict(DEFAULT_PALETTE)
    art = Image.open(sec["art"]).convert("RGB")
    harmonize_palette(pal, dominant_color(art))
    overrides = data.get("palette") or {}
    for k, v in overrides.items():
        pal[k] = hex_to_rgb(v) if isinstance(v, str) else tuple(v)
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
                draw_coin(d, x0 + k * (gs + 6) + gs // 2, cy, gs // 2)

    win_w = cw - 88
    win_h = art_b - name_b - 18
    c.paste(art_with_fade(art, win_w, win_h, frame_rgb=pal["bg"]), (44, name_b + 4))
    d.rectangle([44, name_b + 4, 44 + win_w - 1, name_b + 4 + win_h - 1],
                outline=pal["gold2"], width=3)

    d.text((cw // 2, (art_b + type_b) // 2 + 2), sec["type_line"],
           font=ImageFont.truetype(fonts["i"], 28), fill=pal["subtitle"], anchor="mm")

    has_extra = bool(sec.get("extra_label"))
    r_bottom = int(ch * 0.81) if has_extra else rule_b
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
        d.rounded_rectangle([MARGIN_X, r_bottom + 10, cw - MARGIN_X - 1, extra_b], radius=14,
                            fill=pal["band"], outline=pal["gold"], width=3)
        d.text((cw // 2, (r_bottom + 10 + extra_b) // 2 - 16), sec["extra_label"],
               font=ImageFont.truetype(fonts["r"], 26), fill=pal["subtitle"], anchor="mm")
        d.text((cw // 2, (r_bottom + 10 + extra_b) // 2 + 18), sec["extra_value"],
               font=ImageFont.truetype(fonts["b"], 32), fill=pal["text_light"], anchor="mm")

    foot_t = extra_b + 8
    d.rectangle([26, foot_t, cw - 27, ch - 27], fill=pal["footer"], outline=pal["gold"], width=3)
    ff = ImageFont.truetype(fonts["r"], 24)
    d.text((48, (foot_t + ch - 27) // 2), sec.get("footer_left", ""), font=ff,
           fill=pal["footer_txt"], anchor="lm")
    d.text((cw - 48, (foot_t + ch - 27) // 2), sec.get("footer_right", ""), font=ff,
           fill=pal["footer_txt"], anchor="rm")
    return c
