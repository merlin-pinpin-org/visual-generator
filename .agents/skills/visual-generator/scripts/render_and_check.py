#!/usr/bin/env python3
"""Skill helper: batch-render + OCR-check a set of JSON visuals.

Given one or more ``--data`` JSON files (or a directory scanned for
``*.json``), renders each with the installed visual-generator library
and runs the fail-closed OCR check on every output. Use after editing
data or art so no visual is delivered unvalidated.

Usage::

    python render_and_check.py --data docs/visuals/data/match.json
    python render_and_check.py --data docs/tcg/data/

Environment: same as the library (OCR_CHECK_ALLOW_MISSING_TESSERACT=1
downgrades the OCR step in sandboxes without tesseract).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys


def collect(paths):
    files = []
    for p in paths:
        if os.path.isdir(p):
            files += sorted(
                os.path.join(p, f) for f in os.listdir(p) if f.endswith(".json")
            )
        else:
            files.append(p)
    return files


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data", nargs="+", required=True, help="JSON visual file(s) or directory")
    args = ap.parse_args()
    from engine.render import main as render_main  # noqa: F401  (documentation)
    import engine.render as render_mod
    import tools.ocr_check as check_mod

    failures = []
    for path in collect(args.data):
        sys.argv = ["vg-render", "--data", path]
        try:
            render_mod.main()
        except SystemExit as e:
            if e.code:
                failures.append(("render", path))
                continue
        sys.argv = ["vg-ocr-check", "--data", path]
        try:
            check_mod.main()
        except SystemExit as e:
            if e.code:
                failures.append(("ocr", path))
    if failures:
        sys.exit(f"failed: {failures}")
    print(f"ok: {len(collect(args.data))} visual(s) rendered and checked")


if __name__ == "__main__":
    main()
