#!/usr/bin/env python3
"""Template: match announcement (Discord-sized, crest-centered).

Landscape 1200×675 (Discord embed ratio). Composition, left to right:

- **attacker side** (left): large crest, kingdom name below, then up to
  3 civilization icons (the civs fielded by the attacker) in a row;
- **center**: the battle map thumbnail in a gold medallion, map name
  under it, VS badge between the two kingdoms;
- **defender side** (right): large crest, kingdom name below;
- backdrop: a dim battle scene, no empty plate zones — every zone
  carries image or text.

JSON schema::

    {
      "template": "match_announcement",
      "output": "examples/match.jpg",
      "art": "path/to/battle_backdrop.jpg",
      "sections": {
        "left_name": "Royaume des HeN",
        "left_crest": "path/to/blason.png",
        "left_civs": ["path/civ1.png", "path/civ2.png"],  # max 3 shown
        "right_name": "Royaume d'Ellenseg",
        "right_crest": "path/to/blason.png",
        "map_art": "path/to/map_thumbnail.png",
        "map_name": "Arabie",
        "vs": "VS",
        "context_line": "Attaque — Cycle 3",
        "sub_line": "Dimanche 23 h 30 · Saison II",
        "footer": "Mod Kingdoms"
      }
    }
"""
from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

DEFAULT_PALETTE = {
    "bg": (24, 20, 16), "band": (52, 40, 24), "gold": (176, 141, 74),
    "text_light": (238, 220, 168), "subtitle": (205, 180, 130),
    "vs_bg": (176, 44, 32), "vs_ring": (218, 193, 121), "vs_txt": (255, 240, 210),
}

W, H = 1200, 675
CREST = 230
MEDAL = 200
CIV_ICON = 56


def crop_to(art, w, h):
    """Center-crop art to the w:h window (no stretching)."""
    aw, ah = art.size
    scale = max(w / aw, h / ah)
    big = art.resize((int(aw * scale), int(ah * scale)))
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
        c.paste(Image.blend(c, art, 0.55), (0, 0))
    d.rectangle([0, 0, W - 1, H - 1], outline=pal["gold"], width=8)

    # --- attacker (left) ---
    lcx = 235
    crest = Image.open(sec["left_crest"]).convert("RGBA")
    crest.thumbnail((CREST, CREST))
    c.paste(crest, (lcx - crest.width // 2, 205 - crest.height // 2), crest)
    d.text((lcx, 340), sec["left_name"], font=ImageFont.truetype(fonts["b"], 38),
           fill=pal["text_light"], anchor="mm")
    civs = sec.get("left_civs", [])[:3]
    if civs:
        total = len(civs) * CIV_ICON + (len(civs) - 1) * 10
        x = lcx - total // 2
        for icon_path in civs:
            icon = Image.open(icon_path).convert("RGBA")
            icon.thumbnail((CIV_ICON, CIV_ICON))
            c.paste(icon, (x, 385), icon)
            x += CIV_ICON + 10

    # --- defender (right) ---
    rcx = W - 235
    crest = Image.open(sec["right_crest"]).convert("RGBA")
    crest.thumbnail((CREST, CREST))
    c.paste(crest, (rcx - crest.width // 2, 205 - crest.height // 2), crest)
    d.text((rcx, 340), sec["right_name"], font=ImageFont.truetype(fonts["b"], 38),
           fill=pal["text_light"], anchor="mm")

    # --- battle map medallion (center) ---
    m = MEDAL
    mcx, mcy = W // 2, 205
    map_img = crop_to(Image.open(sec["map_art"]).convert("RGB"), m, m)
    mask = Image.new("L", (m, m), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, m - 1, m - 1], fill=255)
    c.paste(map_img, (mcx - m // 2, mcy - m // 2), mask)
    d.ellipse([mcx - m // 2, mcy - m // 2, mcx + m // 2, mcy + m // 2],
              outline=pal["gold"], width=6)
    d.text((mcx, mcy + m // 2 + 32), sec.get("map_name", ""),
           font=ImageFont.truetype(fonts["b"], 32), fill=pal["text_light"], anchor="mm")

    # --- VS badge between the kingdoms ---
    r = 46
    cy = 205
    d.ellipse([mcx - 230 - r, cy - r, mcx - 230 + r, cy + r],
              fill=pal["vs_bg"], outline=pal["vs_ring"], width=4)
    d.text((mcx - 230, cy), sec.get("vs", "VS"),
           font=ImageFont.truetype(fonts["b"], 36), fill=pal["vs_txt"], anchor="mm")

    # --- bottom band: context (no empty zones) ---
    d.rectangle([70, 470, W - 70, 545], fill=pal["band"], outline=pal["gold"], width=3)
    d.text((W // 2, 507), sec["context_line"], font=ImageFont.truetype(fonts["b"], 34),
           fill=pal["text_light"], anchor="mm")
    d.text((W // 2, 575), sec.get("sub_line", ""), font=ImageFont.truetype(fonts["r"], 24),
           fill=pal["subtitle"], anchor="mm")
    d.text((W // 2, 615), sec.get("footer", ""), font=ImageFont.truetype(fonts["r"], 20),
           fill=pal["subtitle"], anchor="mm")
    return c
