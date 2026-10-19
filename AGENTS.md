# AGENTS.md — visual-generator

Instructions for AI coding agents working in this repository.

## What this repo is

A data-driven visual generator: **JSON + template + art + text
sections**. The Kingdoms Discord bot uses it for TCG cards, match
announcements, galleries and annotated world maps. The long-term goal
is a pip-installable library (see the `lib` issue) — keep the engine
template-agnostic and the Kingdoms specifics in `data/`.

## Non-negotiable rules

1. **The image model never renders text.** All visible words are drawn
   by the engine from the JSON with a real vector font. This is the
   only way to guarantee correct text, and it is what makes every
   output OCR-verifiable.
2. **Every rendered output must pass `tools/ocr_check.py`** before it
   is committed or delivered. The check is fail-closed.
3. **Data is the source of truth.** To change a visual, edit the JSON
   and re-render. Never edit a rendered image.
4. **Templates own the layout.** Zone positions are fixed canvas
   fractions; art is center-cropped into its window and must never
   shift text zones. If a text box moves depending on the art, the
   template is wrong — fix the template.
5. **Assets are content.** The JSON references the real game assets
   (kingdom crests, map thumbnails, civilization icons). The renderer
   places what it is given; it never invents or substitutes assets.
6. **Maps need geographic care.** Before pinning regions on a
   `world_map`, inspect the map art and place each territory on
   actual land at its geographic position. Pins in the ocean are a
   defect.
7. **Art URLs from image generation expire (~1 h).** Download
   immediately; deliver via committed files (raw GitHub URLs), never
   via generated links or sandbox paths.

## Workflow

1. Write/extend the JSON in `data/` (schema in the template docstring).
2. Render: `python engine/render.py --data data/<name>.json`.
3. Validate: `python tools/ocr_check.py --data data/<name>.json`, plus
   a visual check for layout defects.
4. Commit JSON + art + rendered output together, with a message
   naming the template.

## Adding a template

- One module per visual kind in `templates/`, exposing
  `render(data, fonts)` and `DEFAULT_PALETTE` (palette keys documented,
  hex overrides allowed from the JSON `palette` key).
- Document the JSON schema in the module docstring, with a working
  example.
- `engine/render.py` injects `resolve_palette` into the template
  module — templates never import the engine.
- Ship a `data/` example and validate its rendering by OCR.
- Keep assets small: example images ≤ ~300 KB, meaningful names.

## Style

- Python: fail-closed (explicit errors, non-zero exits, no partial
  writes), documented docstrings, no comments noise.
- Commits: `area: what changed` (e.g. `template: match_announcement
  crests`).
