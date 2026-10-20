"""End-to-end tests: render every data/*.json example, then OCR-check.

Renders use the JSON's own ``output`` path — the same contract as
``make render`` / ``make check``. Tesseract is an optional dependency:
without it the OCR step degrades to the documented dev-sandbox skip
(tools/ocr_check.py) instead of failing.
"""
import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO, "data")


def test_art_provider_placeholder(tmp_path):
    from engine.art import SolidArtProvider, get_provider

    p = get_provider("solid")
    assert isinstance(p, SolidArtProvider)
    out = str(tmp_path / "art.png")
    assert p.generate("forest knights", out, 64, 48) == out
    from PIL import Image
    img = Image.open(out)
    assert img.size == (64, 48)
    out2 = p.generate("forest knights", str(tmp_path / "art2.png"), 64, 48)
    assert (Image.open(out2).convert("RGB").getpixel((0, 0))
            == img.convert("RGB").getpixel((0, 0)))


def test_get_provider_unknown():
    import pytest

    from engine.art import get_provider

    with pytest.raises(ValueError):
        get_provider("nope")


def test_list_templates():
    from engine.render import list_templates

    names = list_templates()
    for expected in ("card_tcg", "entity_card", "match_announcement",
                     "world_map", "gallery", "parchment_poster",
                     "contact_sheet"):
        assert expected in names, names


def test_unknown_template_fails_closed(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"template": "nope", "output": "x.jpg",
                               "sections": {}}), encoding="utf-8")
    r = subprocess.run(
        [sys.executable, os.path.join(REPO, "engine", "render.py"),
         "--data", str(bad)],
        capture_output=True, text=True)
    assert r.returncode != 0
    assert "unknown template" in (r.stdout + r.stderr)


def test_examples_render_and_check():
    data_files = sorted(f for f in os.listdir(DATA_DIR) if f.endswith(".json"))
    assert data_files, "no example data files found"
    for name in data_files:
        path = os.path.join(DATA_DIR, name)
        data = json.load(open(path, encoding="utf-8"))
        assert os.path.isfile(os.path.join(REPO, data["output"])), \
            (name, "art/output asset missing")
        r = subprocess.run(
            [sys.executable, os.path.join(REPO, "engine", "render.py"),
             "--data", path],
            capture_output=True, text=True)
        assert r.returncode == 0, (name, r.stderr)
        check = subprocess.run(
            [sys.executable, os.path.join(REPO, "tools", "ocr_check.py"),
             "--data", path],
            capture_output=True, text=True)
        assert check.returncode == 0, (name, check.stdout, check.stderr)
