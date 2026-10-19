---
name: visual-generator
description: Generate any game visual (TCG cards, match announcements, galleries, annotated world maps) from JSON data + templates + art, with OCR-verified text. Use when the game designer asks for card art, announcement banners, decks, illustrated rules, or any branded image.
---

# Visual generation (visual-generator)

**Repository**: https://github.com/merlin-pinpin-org/visual-generator
The repo is the source of truth: engine, templates, JSON data
schemas, examples, this skill's companion instructions
(`AGENTS.md`).

## The one hard rule

**The image model never renders text.** It produces convincing-looking
but misspelled pseudo-text. All text is drawn by the engine from the
JSON with a real vector font — that is what makes the output provable
by OCR. Never "save time" by asking the image model to write words.

## Pipeline (per visual)

1. **Data** — write `data/<name>.json` following the template's schema
   (documented in the template module docstring; live examples in
   `data/`). The JSON references real game assets (crests, map
   thumbnails, civ icons) — assets are content, the renderer only
   places them.
2. **Art** — for art the game does not already provide, one
   image-generation call per visual, always with: `NO text, NO
   letters, NO words anywhere`. For maps: also demand region shapes
   you can pin territories onto, and **inspect the generated art
   before placing pins** — territories must sit on actual land
   (Americas west, Europe center-north, Africa center-south, Asia
   east).
3. **Download the art immediately** — generated URLs expire (~1 h).
   Never share an expired link or a sandbox path with the user:
   deliver through committed files (raw GitHub URLs).
4. **Render** — `python engine/render.py --data data/<name>.json`.
   Dependencies: `pip install pillow` (fonts auto-located via
   matplotlib's DejaVu Serif bundle).
5. **Validate — mandatory.** Run `python tools/ocr_check.py --data
   data/<name>.json` (fail-closed: exits non-zero if any expected
   string is missing from the OCR transcript). Complete with a visual
   check for layout defects (cropped or overlapping text, elements in
   the water on maps, cost icons legible).
6. **Commit** the JSON, the art and the rendered output together.

## Templates

- `card_tcg` — TCG card. Fixed anatomy (name banner / art window /
  type line / rule box / extra box / footer as fixed canvas
  fractions — the art never shifts text zones). Cost: `cost` is an
  int, drawn as N gear icons (Magic-style repeated currency icons).
- `match_announcement` — Discord-sized (1200×675) X-vs-Y banner:
  large crests centered per side, kingdom names below, attacker's civ
  icons (max 3) under the name, battle-map medallion in the center,
  VS badge, context band. Dim battle backdrop, no empty zones.
- `gallery` — titled grid of art+caption items (territories, civs).
- `world_map` — real map art background with geo-placed region pins.

New template? Copy an existing one, keep the contract: `render(data,
fonts)` + `DEFAULT_PALETTE`, document the JSON schema in the
 docstring, ship a `data/` example and validate it.

## Known pitfalls (all learned the hard way)

- Image-model text is gibberish — see the hard rule.
- Art URLs expire (~1 h) — download immediately.
- Pins placed without inspecting the map art end up in the ocean —
  always check the generated map first.
- Text over busy art fails OCR — flatten a plate behind it (see the
  world_map template).
- Fonts: DejaVu Serif located via matplotlib; `--font-dir` overrides.
- Binary assets in git: keep example assets small (≤ ~300 KB each)
  and meaningful names (`crest_hen.png`, not `Gr508B4g-hen.png`).
