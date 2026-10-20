#!/usr/bin/env python3
"""Template: entity card — one entity's sheet, collector-card style.

The proven collector-card anatomy: outer frame, colored name banner
with a badge, a large art window over a translucent backdrop, parchment
plates for the content (light box, dark ink — the OCR-winning
contrast), an optional linked-value box, and a dark footer. Built for
the "one entity per post" visuals: civilization sheet, map sheet,
player profile.

JSON schema::

    {
      "template": "entity_card",
      "output": "examples/entity_faction.jpg",
      "canvas": {"width": 744, "height": 1032},        # optional (card ratio)
      "palette": {"gold": "#5c8a4e", "band": "#22301e"},  # kind colors
      "art": "path/to/entity_art.jpg",                  # the art window
      "backdrop": "path/to/scene.jpg",                  # optional: diffuse background
      "badge": "aoe2",                                  # round badge, optional
      "sections": {
        "title": "Byzantins",
        "type_line": "Civilisation défensive",
        "plates": [
          {"head": "Bonus de civilisation",
           "lines": ["Bâtiments +10/20/30/40 % de PV", "..."]}
        ],
        "extra_label": "Unité unique",                  # optional linked box
        "extra_value": "Cataphractaire",
        "footer_left": "faction:aoe2:Byzantines",
        "footer_right": "Demo Game"
      }
    }

The optional ``backdrop`` is a scene art stretched behind the whole
card and lightly veiled (18% toward the band color), barely blurred: the
scene stays readable — it is a backdrop, not a wash (v6: a too-
diffuse backdrop is a flat fill).

Anatomy (fractions of the canvas — never moved by the art):

    0.00–0.10  outer frame + name banner (badge on the right)
    0.10–0.55  art window (full-bleed, center-cropped)
    0.55–0.58  italic type line
    0.58–0.86  parchment plate: section heads + lines
    0.86–0.94  linked-value box (banner color, when extra is set)
    0.94–1.00  footer
"""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFilter, ImageFont

DEFAULT_PALETTE = {
    "bg": (30, 38, 26), "band": (34, 48, 30), "gold": (92, 138, 78),
    "gold2": (66, 96, 58), "text_light": (224, 238, 210),
    "subtitle": (200, 216, 190), "box": (238, 232, 208), "ink": (30, 40, 22),
    "badge": (52, 92, 44), "badge_ring": (224, 238, 210),
    "badge_txt": (240, 250, 235), "footer": (34, 48, 30),
    "footer_txt": (200, 216, 190),
}

F_NAME = 0.10
F_ART = 0.55
F_TYPE = 0.58
F_RULE = 0.86
F_EXTRA = 0.94

MARGIN_X = 56


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


def _fit(img, w, h):
    """Scale to fit inside w×h (contain), centered, transparency kept."""
    img = img.copy()
    img.thumbnail((w - 24, h - 24))
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    layer.paste(img, ((w - img.width) // 2, (h - img.height) // 2))
    return layer


def _crop(art, w, h, bg=(30, 38, 26)):
    """Center-crop art to the w:h window; transparency composites on bg."""
    if art.mode in ("P", "LA", "RGBA"):
        rgba = art.convert("RGBA")
        base = Image.new("RGBA", rgba.size, bg + (255,))
        art = Image.alpha_composite(base, rgba).convert("RGB")
    else:
        art = art.convert("RGB")
    scale = max(w / art.width, h / art.height)
    big = art.resize((int(art.width * scale), int(art.height * scale)))
    x, y = (big.width - w) // 2, (big.height - h) // 2
    return big.crop((x, y, x + w, y + h))


def render(data, fonts):
    sec = data["sections"]
    pal = resolve_palette(DEFAULT_PALETTE, data.get("palette"))
    cw = data.get("canvas", {}).get("width", 744)
    ch = data.get("canvas", {}).get("height", 1032)
    c = Image.new("RGBA", (cw, ch), pal["bg"] + (255,))
    backdrop = data.get("backdrop")
    if backdrop:
        bd = Image.open(backdrop).convert("RGB").resize((cw, ch))
        bd = bd.filter(ImageFilter.GaussianBlur(2))
        veil = Image.new("RGB", (cw, ch), pal["band"])
        c.paste(Image.blend(bd, veil, 0.18).convert("RGBA"), (0, 0))
    d = ImageDraw.Draw(c)

    name_b = int(ch * F_NAME)
    art_b = int(ch * F_ART)
    type_b = int(ch * F_TYPE)
    rule_b = int(ch * F_RULE)
    extra_b = int(ch * F_EXTRA)

    # --- outer frame + name banner (the deck's double frame) ---
    d.rectangle([0, 0, cw - 1, ch - 1], outline=pal["gold"], width=10)
    d.rectangle([16, 16, cw - 17, ch - 17], outline=pal["gold2"], width=3)
    d.rectangle([26, 26, cw - 27, name_b], fill=pal["band"], outline=pal["gold"], width=3)
    nf = ImageFont.truetype(fonts["b"], 48 if len(sec["title"]) <= 12 else 40)
    d.text((72, (26 + name_b) // 2), sec["title"], font=nf,
           fill=pal["text_light"], anchor="lm")

    badge = data.get("badge")
    if badge:
        r = 40
        cx, cy = cw - 96, (26 + name_b) // 2
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=pal["badge"],
                  outline=pal["badge_ring"], width=4)
        cf = ImageFont.truetype(fonts["b"], 30 if len(str(badge)) > 3 else 48)
        d.text((cx, cy), str(badge), font=cf, fill=pal["badge_txt"], anchor="mm")

    # --- art window ---
    # The window itself stays translucent (the backdrop shows through);
    # transparent art (crests) composites over the backdrop, never on an
    # opaque fill — v6: a transparent crest must let the scene breathe.
    win_w = cw - 128
    win_h = art_b - name_b - 18
    win_plate = Image.new("RGBA", (win_w, win_h), (0, 0, 0, 0))
    art = Image.open(data["art"])
    if art.mode in ("P", "LA", "RGBA"):
        rgba = art.convert("RGBA")
        fitted = _fit(rgba, win_w, win_h)
        win_plate = Image.alpha_composite(win_plate, fitted)
    else:
        win_plate = _crop(art.convert("RGB"), win_w, win_h).convert("RGBA")
    c.alpha_composite(win_plate, (64, name_b + 4))
    d.rectangle([64, name_b + 4, 64 + win_w - 1, name_b + 4 + win_h - 1],
                outline=pal["gold2"], width=3)

    # --- italic type line ---
    d.text((cw // 2, (art_b + type_b) // 2 + 2), sec.get("type_line", ""),
           font=ImageFont.truetype(fonts["i"], 28), fill=pal["subtitle"], anchor="mm")

    # --- parchment plate: heads + lines (the deck's rule box) ---
    has_extra = bool(sec.get("extra_label"))
    r_bottom = int(ch * 0.81) if has_extra else rule_b
    r_top = type_b + 6
    plate = Image.new("RGBA", (cw, r_bottom - r_top), (0, 0, 0, 0))
    pd = ImageDraw.Draw(plate)
    pd.rounded_rectangle([MARGIN_X, 0, cw - MARGIN_X - 1, r_bottom - r_top - 1], radius=14,
                         fill=tuple(pal["box"]) + (206,), outline=pal["gold2"] + (255,), width=3)
    c.alpha_composite(plate, (0, r_top))
    d = ImageDraw.Draw(c)
    head_f = ImageFont.truetype(fonts["b"], 24)
    body_f = ImageFont.truetype(fonts["r"], 21)
    y = r_top + 16
    for plate in sec.get("plates", []):
        d.text((60, y), plate.get("head", ""), font=head_f, fill=pal["gold2"])
        y += 32
        for item in plate.get("lines", []):
            for ln in _wrap(d, f"• {item}" if not str(item).startswith("•") else str(item),
                            body_f, cw - 2 * MARGIN_X - 44)[:4]:
                d.text((66, y), ln, font=body_f, fill=pal["ink"])
                y += 26
        y += 8
    # vertical centering of the plate content
    # (content is top-aligned; long lists fill the plate naturally)

    # --- linked-value box (banner color) ---
    if has_extra:
        box = Image.new("RGBA", (cw, extra_b - r_bottom - 12), (0, 0, 0, 0))
        bd2 = ImageDraw.Draw(box)
        bd2.rounded_rectangle([MARGIN_X, 0, cw - MARGIN_X - 1, extra_b - r_bottom - 13], radius=14,
                              fill=tuple(pal["band"]) + (216,), outline=pal["gold"] + (255,), width=3)
        c.alpha_composite(box, (0, r_bottom + 12))
        d = ImageDraw.Draw(c)
        d.text((cw // 2, (r_bottom + 12 + extra_b) // 2 - 16), sec["extra_label"],
               font=ImageFont.truetype(fonts["r"], 26), fill=pal["subtitle"], anchor="mm")
        d.text((cw // 2, (r_bottom + 12 + extra_b) // 2 + 18), sec["extra_value"],
               font=ImageFont.truetype(fonts["b"], 32), fill=pal["text_light"], anchor="mm")

    # --- footer ---
    foot_t = extra_b + 8
    d.rectangle([26, foot_t, cw - 27, ch - 27], fill=pal["footer"],
                outline=pal["gold"], width=3)
    ff = ImageFont.truetype(fonts["r"], 24)
    d.text((48, (foot_t + ch - 27) // 2), sec.get("footer_left", ""),
           font=ff, fill=pal["footer_txt"], anchor="lm")
    d.text((cw - 48, (foot_t + ch - 27) // 2), sec.get("footer_right", ""),
           font=ff, fill=pal["footer_txt"], anchor="rm")
    return c
