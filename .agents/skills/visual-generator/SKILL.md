---
name: visual-generator
description: Render game visuals (TCG cards, match announcements, galleries, annotated world maps, parchment rules posters, contact sheets) from JSON data + templates + art, with OCR-verified text. Use whenever a game designer asks for card art, announcement banners, decks, illustrated rules, or any branded image.
---

# Visual generation (visual-generator)

**Repository**: https://github.com/merlin-pinpin-org/visual-generator

The repo is the source of truth: engine, templates, JSON data schemas,
examples, this skill and its companion instructions (`AGENTS.md`).

## The one hard rule

**The image model never renders text.** It produces convincing-looking
but misspelled pseudo-text. All text is drawn by the engine from the
JSON with a real vector font — that is what makes the output provable
by OCR. Never "save time" by asking the image model to write words.

## Install

The library is pip/uv-installable and exposes three CLIs:

```bash
uv pip install visual-generator        # or: pip install visual-generator
```

- `vg-render --data <visual.json>` — render one visual
- `vg-ocr-check --data <visual.json>` — fail-closed OCR validation
- `vg-demo-assets` — regenerate the demo art into `examples/assets/`

In a project managed by uv, add the dependency and sync:

```bash
uv add visual-generator
uv sync
uv run vg-render --data docs/visuals/data/<name>.json
```

Dependencies (installed automatically): `pillow`, `matplotlib` (font
bundle). Fonts auto-locate DejaVu Serif; `--font-dir` overrides.

## Pipeline (per visual)

1. **Data** — write `<name>.json` following the template's schema
   (documented in the template module docstring; live examples in the
   library `data/` directory). The JSON references real game assets
   (crests, map thumbnails, civ icons) — assets are content, the
   renderer only places them. Art paths are repo-relative, never
   sandbox paths.
2. **Art** — for art the game does not already provide, one
   image-generation call per visual, always with: `NO text, NO
   letters, NO words anywhere`. For maps: also demand region shapes
   you can pin territories onto, and **inspect the generated art
   before placing pins** — territories must sit on actual land.
3. **Download the art immediately** — generated URLs expire (~1 h).
   Never share an expired link or a sandbox path with the user:
   deliver through committed files (raw GitHub URLs).
4. **Render** — `vg-render --data <name>.json` (or `python engine/
   render.py --data …` from a repo checkout). The `template` key
   selects the layout module.
5. **Validate — mandatory.** `vg-ocr-check --data <name>.json`
   (fail-closed: non-zero exit if any expected string is missing from
   the OCR transcript; requires tesseract + `fra`). In sandboxes
   without tesseract, `OCR_CHECK_ALLOW_MISSING_TESSERACT=1` downgrades
   to a skip warning — then OCR every image with another available
   engine before delivery. Complete with a visual check for layout
   defects (cropped/overlapping text, pins in the ocean, cost icons
   legible).
6. **Commit** the JSON, the art and the rendered output together, with
   a message naming the template.

## Templates

- `card_tcg` — TCG card. Fixed anatomy (name banner / art window /
  type line / rule box / extra box / footer as fixed canvas fractions
  — the art never shifts text zones). `cost`: int = N gear icons
  (repeated currency icons), string = round text badge (e.g. "T").
  Optional `extra_label`/`extra_value` box (linked value). `palette`
  accepts hex overrides of any documented palette key.
- `contact_sheet` — N card visuals re-rendered side by side on a
  titled dark sheet (`card_template` + `cards` array), aspect kept.
- `match_announcement` — Discord-sized (1200×675) X-vs-Y banner: large
  crests centered per side, names below, attacker's civ icons (max 3)
  under the name, battle-map medallion in the center, VS badge,
  context band. Dim battle backdrop via the top-level `art` key.
- `gallery` — titled grid of art+caption items (territories, civs).
- `world_map` — real map art background with geo-placed region pins
  (`x`/`y` on the 1600×1200 canvas; plates stay readable over busy
  art).
- `parchment_poster` — parchment texture background, titled, auto-
  fitted multi-column rules text, fail-closed when content cannot fit.
- `entity_card` — one entity's sheet, collector-card style: name
  banner + badge, art window over a translucent backdrop, parchment
  plates (sections with heads + lines), optional linked-value box.
  The civilization / map / player card case; replaces long read-only
  embeds. The backdrop stays visible (light veil); transparent art
  (crests) lets it show through.

New template? Copy an existing one, keep the contract: `render(data,
fonts)` + `DEFAULT_PALETTE`, document the JSON schema in the
docstring, ship a `data/` example and validate it by OCR.

## Known pitfalls (all learned the hard way)

- Image-model text is gibberish — see the hard rule.
- Art URLs expire (~1 h) — download immediately.
- Pins placed without inspecting the map art end up in the ocean —
  always check the generated map first.
- Text over busy art fails OCR — flatten a plate behind it (see the
  world_map / parchment_poster templates).
- Sandbox paths in JSON break re-rendering — art paths are always
  repo-relative.
- Binary assets in git: keep example assets small (≤ ~300 KB each)
  and meaningful names (`crest_lion.png`, not `Gr508B4g-lion.png`).
