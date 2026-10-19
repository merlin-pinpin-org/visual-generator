#!/usr/bin/env python3
"""Template: parchment-style rules poster (texture + vector text).

A *background texture* (image model, no text) plus text drawn by the
engine with a real vector font — never by the image model. All content
comes from the JSON, so the same template renders any two-column rule
sheet, quest scroll or seasonal rules poster.

JSON schema::

    {
      "template": "parchment_poster",
      "output": "examples/rules_poster.jpg",
      "art": "path/to/parchment_texture.jpg",
      "sections": {
        "title": "LES RÈGLES DU JEU",
        "subtitle": "Saison I",
        "footer": "— Tel qu'il est écrit, ainsi soit-il joué —",
        "source_line": "Source : docs/rules",
        "columns": 2,
        "sections": [
          {"head": "Les Territoires",
           "body": "Chaque territoire est une carte.\\nSecond paragraph."}
        ]
      }
    }

Sections are distributed over the columns in order. ``body`` supports
``\\n`` paragraph breaks. The layout auto-fits: font sizes shrink until
all columns end above the footer zone; render aborts (fail-closed via
SystemExit) when the content cannot fit at the minimum size.

Layout guards (learned from failed attempts — keep them):

- Wide inner margins (MARGX = 235 px at 1400 px wide): a generated
  parchment texture usually has an ornate border; text must stay clear
  of it.
- Dark ink on light parchment, bold + stroke for the title: plain brown
  on a textured background fails OCR.
"""

from __future__ import annotations

import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

DEFAULT_PALETTE = {
    "ink": (62, 42, 22), "ink_dark": (40, 26, 12),
    "fade": (94, 66, 34), "stroke": (235, 224, 196),
    "plate": (240, 228, 200),
}

W, H = 1400, 2050          # poster canvas
MARGX = 235                # inner margin: clear of the ornate border
GUTTER = 70                # gap between columns
YTOP = 310                 # first section baseline
YBOTTOM = 1750             # content must end above this
MIN_BODY, MIN_HEAD, MIN_LH = 20, 26, 30  # fail-closed floor


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


def measure_column(draw, sections, fonts, colw):
    """Total height of a column at current sizes; returns per-paragraph
    line lists so the caller does not recompute."""
    body_f, head_f, lh = fonts["body"], fonts["head"], fonts["lh"]
    heights = []
    for sec in sections:
        paragraphs = [wrap(draw, para, body_f, colw) or [""] for para in sec["body"].split("\n")]
        h = 0
        for pl in paragraphs:
            h += len(pl) * lh
        h += len(paragraphs) * 6          # inter-paragraph gap
        h += head_f.size + 16 + 30        # heading + heading gap + section gap
        heights.append((sec, paragraphs, h))
    return heights


def render(data, fonts):
    sec = data["sections"]
    pal = resolve_palette(DEFAULT_PALETTE, data.get("palette"))
    tex = Image.open(data["art"]).convert("RGB")
    img = ImageEnhance.Brightness(tex.resize((W, H))).enhance(1.08)
    # Flatten the ornate texture behind the title and footer zones so the
    # vector text stays high-contrast and OCR-verified (parchment tint,
    # 60% opacity: keeps the aged look, kills the background noise).
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    plate = tuple(pal["plate"]) + (155,)
    od.rectangle([W // 2 - 560, 60, W // 2 + 560, 250], fill=plate)
    od.rounded_rectangle([W // 2 - 540, 1860, W // 2 + 540, 1995], radius=20, fill=plate)
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    d = ImageDraw.Draw(img)
    d.text((W // 2, 130), sec["title"], font=ImageFont.truetype(fonts["b"], 68),
           fill=pal["ink_dark"], anchor="mm", stroke_width=2, stroke_fill=pal["stroke"])
    d.text((W // 2, 205), sec.get("subtitle", ""), font=ImageFont.truetype(fonts["b"], 34),
           fill=pal["ink_dark"], anchor="mm")
    d.line([(W // 2 - 260, 250), (W // 2 + 260, 250)], fill=pal["fade"], width=3)
    ncols = sec.get("columns", 2)
    colw = (W - 2 * MARGX - (ncols - 1) * GUTTER) // ncols
    sections = sec["sections"]
    per_col = (len(sections) + ncols - 1) // ncols
    cols = [sections[i * per_col:(i + 1) * per_col] for i in range(ncols)]
    # Auto-fit: shrink until every column fits above YBOTTOM.
    body_size, head_size, lh = 23, 30, 35
    while body_size >= MIN_BODY:
        fnt = {
            "body": ImageFont.truetype(fonts["r"], body_size),
            "head": ImageFont.truetype(fonts["b"], head_size),
            "lh": lh,
        }
        laid = [measure_column(d, col, fnt, colw) for col in cols]
        tops = [YTOP + sum(h for _, _, h in c) for c in laid]
        if all(t <= YBOTTOM for t in tops):
            break
        body_size -= 1
        head_size = max(MIN_HEAD, head_size - 1)
        lh = max(MIN_LH, lh - 1)
    else:
        sys.exit("poster: content does not fit at minimum font size — split sections")
    xs = [MARGX + i * (colw + GUTTER) for i in range(ncols)]
    for x, laid_sec in zip(xs, laid):
        y = YTOP
        for s, paragraphs, _ in laid_sec:
            d.text((x, y), s["head"], font=fnt["head"], fill=pal["ink"])
            y += fnt["head"].size + 16
            for pl in paragraphs:
                for ln in pl:
                    d.text((x, y), ln, font=fnt["body"], fill=pal["ink"])
                    y += fnt["lh"]
                y += 6
            y += 30
    d.text((W // 2, 1900), sec.get("footer", ""), font=ImageFont.truetype(fonts["i"], 30),
           fill=pal["ink_dark"], anchor="mm")
    d.text((W // 2, 1960), sec.get("source_line", ""), font=ImageFont.truetype(fonts["r"], 26),
           fill=pal["ink_dark"], anchor="mm")
    return img
