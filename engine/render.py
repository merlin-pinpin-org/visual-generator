#!/usr/bin/env python3
"""Core renderer of the visual engine.

A **visual** is a JSON document rendered by a **template** (a Python
layout module). The JSON always carries:

- ``template``   — template name; selects ``templates/<name>.py``
- ``output``     — output image path
- ``canvas``     — optional: ``{"width": int, "height": int}``
- ``palette``    — optional: dict of color overrides (hex strings)
- ``art``        — optional: path(s) to generated art (no text)
- ``sections``   — the content; schema defined per template

Everything the engine draws uses a real vector font — the image model
never renders text (see README, principle 1). The renderer is
fail-closed: unknown template, missing section field, unreadable art
or missing fonts abort with a non-zero exit and an explicit message.

Usage::

    python engine/render.py --data data/visual.json
    python engine/render.py --data data/visual.json --out out.jpg
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("Pillow is required: pip install pillow")

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")


def load_fonts(font_dir: str | None = None) -> dict:
    """Locate DejaVu Serif faces: --font-dir, matplotlib bundle, system."""
    candidates = []
    if font_dir:
        candidates.append(font_dir)
    try:
        import matplotlib

        candidates.append(
            os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf")
        )
    except ImportError:
        pass
    candidates += [
        os.path.expanduser("~/.local/lib/python3.12/site-packages/matplotlib/mpl-data/fonts/ttf"),
        "/usr/share/fonts/truetype/dejavu",
    ]
    for d in candidates:
        if os.path.isfile(os.path.join(d, "DejaVuSerif-Bold.ttf")):
            return {
                "b": os.path.join(d, "DejaVuSerif-Bold.ttf"),
                "r": os.path.join(d, "DejaVuSerif.ttf"),
                "i": os.path.join(d, "DejaVuSerif-Italic.ttf"),
            }
    sys.exit("DejaVu Serif fonts not found")


def hex_to_rgb(value: str):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def resolve_palette(base: dict, overrides: dict | None) -> dict:
    """Merge JSON palette overrides (hex strings) over the template base."""
    pal = dict(base)
    for key, value in (overrides or {}).items():
        pal[key] = hex_to_rgb(value)
    return pal


def import_template(name: str):
    """Load templates/<name>.py; fail-closed when absent or invalid."""
    path = os.path.join(TEMPLATE_DIR, f"{name}.py")
    if not os.path.isfile(path):
        sys.exit(f"unknown template: {name!r} (expected {path})")
    spec = importlib.util.spec_from_file_location(f"template_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "render"):
        sys.exit(f"template {name!r} has no render(data, fonts) function")
    return module


def render_visual(data: dict, font_dir: str | None = None, out: str | None = None) -> str:
    """Render one in-memory visual definition; returns the output path.

    Library entry point for programmatic use (bot integrations,
    drivers): same fail-closed contract as the CLI. ``data`` is the
    visual dict (``template``, ``output``, ``sections``…).
    """
    if out:
        data = {**data, "output": out}
    fonts = load_fonts(font_dir)
    module = import_template(data["template"])
    module.resolve_palette = resolve_palette  # injected, templates never import engine
    img = module.render(data, fonts)
    dest = data["output"]
    os.makedirs(os.path.dirname(os.path.abspath(dest)), exist_ok=True)
    if img.mode == "RGBA" and not dest.lower().endswith(".png"):
        img = img.convert("RGB")  # JPEG: flatten translucent plates onto the backdrop
    img.save(dest, quality=93)
    print("ok", dest)
    return dest


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a JSON visual with a template")
    parser.add_argument("--data", required=True, help="JSON visual definition")
    parser.add_argument("--out", default=None, help="override the JSON output path")
    parser.add_argument("--font-dir", default=None, help="DejaVu Serif directory (auto-detected)")
    args = parser.parse_args()

    with open(args.data, encoding="utf-8") as fh:
        data = json.load(fh)

    render_visual(data, args.font_dir, args.out)


if __name__ == "__main__":
    main()
