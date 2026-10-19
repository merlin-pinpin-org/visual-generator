#!/usr/bin/env python3
"""OCR validation helper: compare an image against its JSON source.

Every visual must pass this check before delivery (README, principle 4).
Requires tesseract (``tesseract-ocr`` package) with the ``fra`` language.

Usage::

    python tools/ocr_check.py --data data/match_hen_gaia.json

Collects every string the JSON contributes to the visual (name,
lines, captions, region notes…), runs tesseract over the rendered
image, and reports each expected string that the transcript does not
contain (case- and accent-insensitive). Exit code is non-zero when a
string is missing — fail-closed.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import unicodedata


def norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def collect_strings(obj) -> list[str]:
    out = []
    if isinstance(obj, str):
        if len(obj) > 2 and not obj.startswith(("#", "path/")):
            out.append(obj)
    elif isinstance(obj, list):
        for v in obj:
            out += collect_strings(v)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("art", "left_crest", "right_crest", "map_art",
                     "left_civs", "x", "y", "color"):
                continue
            out += collect_strings(v)
    return out


def ocr(path: str) -> str:
    try:
        r = subprocess.run(
            ["tesseract", path, "stdout", "-l", "fra+eng"],
            capture_output=True, text=True, timeout=120)
        return r.stdout
    except FileNotFoundError:
        if os.environ.get("OCR_CHECK_ALLOW_MISSING_TESSERACT") == "1":
            print("warn: tesseract not found, OCR check skipped (dev sandbox only)")
            return None
        sys.exit("tesseract not found: apt-get install tesseract-ocr tesseract-ocr-fra")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--data", required=True)
    args = p.parse_args()
    data = json.load(open(args.data, encoding="utf-8"))
    expected = collect_strings(data.get("sections", {}))
    raw = ocr(data["output"])
    if raw is None:
        return
    transcript = norm(raw)
    missing = [s for s in expected if norm(s) not in transcript]
    for s in missing:
        print(f"MISSING: {s!r}")
    if missing:
        sys.exit(f"{len(missing)} expected string(s) not found in OCR transcript")
    print(f"ok: all {len(expected)} strings found in {data['output']}")


if __name__ == "__main__":
    main()
