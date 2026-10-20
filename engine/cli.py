#!/usr/bin/env python3
"""Grouped ``vg`` CLI: render, check, templates, providers.

Sub-commands mirror the module CLIs (``vg-render``, ``vg-ocr-check``)::

    vg render --data data/card_ambush.json
    vg check --data data/card_ambush.json
    vg templates
    vg providers
"""
from __future__ import annotations

import argparse
import json
import sys

from engine.art import PROVIDERS
from engine.render import list_templates


def main() -> None:
    parser = argparse.ArgumentParser(prog="vg", description="Visual generator CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_render = sub.add_parser("render", help="render a JSON visual")
    p_render.add_argument("--data", required=True)
    p_render.add_argument("--out", default=None)
    p_render.add_argument("--font-dir", default=None)

    p_check = sub.add_parser("check", help="OCR-check a rendered visual")
    p_check.add_argument("--data", required=True)

    sub.add_parser("templates", help="list available template names")
    sub.add_parser("providers", help="list available art providers")

    args = parser.parse_args()

    if args.cmd == "render":
        from engine.render import render_visual

        with open(args.data, encoding="utf-8") as fh:
            data = json.load(fh)
        render_visual(data, args.font_dir, args.out)
    elif args.cmd == "check":
        from tools.ocr_check import main as check_main

        sys.argv = ["vg-ocr-check", "--data", args.data]
        check_main()
    elif args.cmd == "templates":
        print("\n".join(list_templates()))
    elif args.cmd == "providers":
        print("\n".join(sorted(PROVIDERS)))


if __name__ == "__main__":
    main()
