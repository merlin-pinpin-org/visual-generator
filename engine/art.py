#!/usr/bin/env python3
"""ArtProvider: generate art (no text) from a prompt.

An ``ArtProvider`` turns a text prompt into a text-free image file.
The engine never renders text with the art provider — visible words
are always drawn by the engine from the JSON (README, principle 1).
Real providers (Mistral, BFL…) are the user's responsibility: they
bring their own API keys and implement the same interface. This
module ships only a placeholder so the library works out of the box
without any key.

Interface::

    class MyProvider(ArtProvider):
        name = "my-provider"

        def generate(self, prompt: str, out_path: str,
                     width: int = 1024, height: int = 1024) -> str:
            ...  # write the image to out_path, return out_path
"""
from __future__ import annotations

import os


class ArtProvider:
    """Abstract base: subclasses set ``name`` and implement ``generate``."""

    name = "abstract"

    def generate(self, prompt: str, out_path: str,
                 width: int = 1024, height: int = 1024) -> str:
        raise NotImplementedError

    def __call__(self, prompt: str, out_path: str,
                 width: int = 1024, height: int = 1024) -> str:
        return self.generate(prompt, out_path, width, height)


class SolidArtProvider(ArtProvider):
    """Placeholder provider: a solid-colored PNG, usable without keys.

    The color derives deterministically from the prompt hash, so the
    same prompt always yields the same backdrop. Real image-model
    providers belong to the consuming project.
    """

    name = "solid"

    def generate(self, prompt: str, out_path: str,
                 width: int = 1024, height: int = 1024) -> str:
        from PIL import Image

        hue = sum(ord(c) for c in prompt) % 360
        rgb = colorsys_hue_to_rgb(hue)
        img = Image.new("RGB", (width, height), rgb)
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        img.save(out_path)
        return out_path


def colorsys_hue_to_rgb(hue: int) -> tuple:
    import colorsys

    r, g, b = colorsys.hsv_to_rgb(hue / 360.0, 0.55, 0.72)
    return (int(r * 255), int(g * 255), int(b * 255))


PROVIDERS: dict[str, ArtProvider] = {p.name: p for p in [SolidArtProvider()]}


def register_provider(provider: ArtProvider) -> None:
    """Register a custom provider under its ``name`` (last one wins)."""
    PROVIDERS[provider.name] = provider


def get_provider(name: str) -> ArtProvider:
    if name not in PROVIDERS:
        try:
            import importlib.metadata as md

            for ep in md.entry_points(group="visual_generator.art_providers", name=name):
                register_provider(ep.load())
        except Exception:
            pass
    try:
        return PROVIDERS[name]
    except KeyError:
        raise ValueError(
            f"unknown art provider: {name!r} (known: {sorted(PROVIDERS)})")
