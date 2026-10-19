# visual-generator

A generic, data-driven visual generator: **JSON + template + art + text
sections**. Any visual — TCG card, match announcement, gallery,
annotated world map — is defined by:

- a **JSON data file** — the content (names, texts, numbers, image paths);
- a **template** — a Python layout module in `templates/`;
- **art** — image-model generated pictures (or real game assets),
  **never carrying text**;
- **text sections** — drawn by the engine with a real vector font,
  which makes every output OCR-verifiable.

## The one hard rule

**The image model never renders text.** Image models produce
convincing-looking but misspelled pseudo-text. Every word on a visual
is drawn by the engine from the JSON — the only way to guarantee
correct text and prove it by OCR.

## Project layout

```
├── engine/render.py       ← core renderer (templates, palettes, fonts)
├── templates/             ← one layout module per visual kind
│   ├── card_tcg.py          TCG card (fixed anatomy, gear-icon costs)
│   ├── match_announcement.py Discord-sized X-vs-Y banner (crests, map
│   │                        medallion, civ icons under the attacker)
│   ├── gallery.py           N-items grid with captions
│   └── world_map.py         annotated map (geo-placed region pins)
├── data/                  ← JSON examples (source of truth per visual)
└── examples/              ← rendered outputs + their assets
```

## Usage

```bash
pip install pillow
python engine/render.py --data data/match_hen_gaia.json
```

The `template` key selects the layout module. Each template documents
its JSON schema in its docstring; each `data/*.json` is a working
example.

## Principles

1. **The image model never renders text** (see above).
2. **Data is the source of truth** — edit the JSON, re-render, never
   edit the image.
3. **Templates own the layout** — zone positions are fixed fractions
   of the canvas; art is center-cropped into its window and never
   shifts the text zones.
4. **Every output must pass OCR** before delivery.
5. **Assets are content, not decoration** — the JSON references the
   real game assets (crests, map thumbnails, civilization icons); the
   renderer places them, it never invents them.

## Status

Prototype, validated on the Kingdoms mod deck (10 technology cards,
48 territory cards, parchment rules poster) and the four templates
above. Roadmap: extract a proper pip-installable library (see the
issues) with a plugin API for templates and art providers.

License: MIT.
