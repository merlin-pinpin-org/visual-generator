#!/usr/bin/env python3
"""Localizable card definitions: properties + per-locale strings.

A **card definition** groups everything about one card::

    {
      "template": "card_tcg",
      "output": "examples/{locale}/card_ambush.jpg",
      "properties": {                    # locale-independent card data
        "cost": 2,
        "art": "examples/assets/card_art_ambush.jpg",
        "footer_left": "1/10",
        "footer_right": "Demo Game"
      },
      "locales": {
        "en": {"name": "Ambush", "type_line": "...", "rule": "..."},
        "fr": {"name": "Embuscade", "type_line": "...", "rule": "..."}
      }
    }

``properties`` and the chosen locale dict are merged into ``sections``
(locale wins on key conflicts). ``output`` contains a ``{locale}``
placeholder. The locale is **required** when rendering or checking a
card definition — extensible: any locale key works, no code change.
"""
from __future__ import annotations

import json
import sys


def is_card_definition(data: dict) -> bool:
    return "locales" in data


def resolve_locale(data: dict, locale: str | None) -> dict:
    """Flatten a card definition into a plain visual dict for ``locale``.

    Fail-closed: missing/unknown locale and missing translation keys
    abort with an explicit message listing what is available/missing.
    A plain visual (no ``locales`` key) passes through untouched.
    """
    if not is_card_definition(data):
        return data
    if not locale:
        available = ", ".join(sorted(data["locales"]))
        sys.exit(f"locale required: choose one of [{available}] (--locale)")
    if locale not in data["locales"]:
        available = ", ".join(sorted(data["locales"]))
        sys.exit(f"unknown locale: {locale!r} (available: [{available}])")

    sections = {**data.get("properties", {}), **data["locales"][locale]}
    if "template" not in data or "output" not in data:
        sys.exit("card definition needs 'template' and 'output' keys")
    out = {
        **{k: v for k, v in data.items()
           if k not in ("locales", "properties", "sections", "output")},
        "output": data["output"].format(locale=locale),
        "sections": sections,
    }
    return out


def load(path: str, locale: str | None) -> dict:
    with open(path, encoding="utf-8") as fh:
        return resolve_locale(json.load(fh), locale)
