#!/usr/bin/env python3
"""Template: contact sheet — one image from N rendered visuals.

Re-renders each card (same data as the individual visuals) and pastes
the results side by side on a titled dark sheet, aspect ratio kept.
Designed for decks: one JSON per card group, one sheet per group.

JSON schema::

    {
      "template": "contact_sheet",
      "output": "examples/sheet.jpg",
      "sections": {
        "title": "MY GAME — Technologies",
        "columns": 5,
        "card_template": "card_tcg",
        "cards": [
          {"sections": {...card schema...}, "canvas": {"width": 744, "height": 1032}},
          {"sections": {...}}
        ]
      }
    }

Each entry of ``cards`` is a full visual definition (minus ``template``
and ``output``) rendered by ``card_template`` at a reduced size on the
sheet. Fail-closed: an invalid card definition aborts the render.
"""

from __future__ import annotations

import importlib.util
import os

from PIL import Image, ImageDraw, ImageFont

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(_ROOT, "templates")

DEFAULT_PALETTE = {
    "bg": (24, 20, 16), "title_txt": (218, 193, 121),
}

MARGIN, GAPX, GAPY = 28, 24, 24
SMALL_W = 488
TITLE_H = 60


def import_template(name):
    path = os.path.join(TEMPLATE_DIR, f"{name}.py")
    if not os.path.isfile(path):
        raise SystemExit(f"contact_sheet: unknown card template {name!r}")
    spec = importlib.util.spec_from_file_location(f"template_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def render(data, fonts):
    sec = data["sections"]
    pal = resolve_palette(DEFAULT_PALETTE, data.get("palette"))
    card_mod = import_template(sec.get("card_template", "card_tcg"))
    if not hasattr(card_mod, "render"):
        raise SystemExit(f"contact_sheet: template {sec.get('card_template')!r} has no render()")
    card_mod.resolve_palette = resolve_palette

    cards = sec["cards"]
    cols = sec.get("columns", 5)
    rows = (len(cards) + cols - 1) // cols
    sample = card_mod.render({"canvas": {}, **cards[0]}, fonts)
    small_h = int(SMALL_W * sample.height / sample.width)
    W = MARGIN * 2 + cols * SMALL_W + (cols - 1) * GAPX
    H = TITLE_H + MARGIN * 2 + rows * small_h + (rows - 1) * GAPY
    sheet = Image.new("RGB", (W, H), pal["bg"])
    d = ImageDraw.Draw(sheet)
    d.text((W // 2, 30), sec.get("title", ""), font=ImageFont.truetype(fonts["b"], 44),
           fill=pal["title_txt"], anchor="mm")
    for i, card in enumerate(cards):
        visual = {"canvas": {}, **card}
        full = card_mod.render(visual, fonts)
        small = full.resize((SMALL_W, small_h))
        r, col = divmod(i, cols)
        x = MARGIN + col * (SMALL_W + GAPX)
        y = TITLE_H + MARGIN + r * (small_h + GAPY)
        sheet.paste(small, (x, y))
    return sheet
