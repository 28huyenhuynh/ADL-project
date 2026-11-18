#!/usr/bin/env python3
"""
Export all 78 tarot cards from the Figma file into static/tarot/.

  1. In Figma: Settings > Security > Personal access tokens > Generate new token
     (scope "File content: Read only" is enough). Copy the token.
  2. Run:   python scripts/export_figma_cards.py --token YOUR_TOKEN
     or     FIGMA_TOKEN=YOUR_TOKEN python scripts/export_figma_cards.py

Cards that already exist in static/tarot/ are skipped (add --all to export everything again).
Uses the official Figma REST API (GET /v1/images), so it does not count against the
Figma MCP tool-call limit. Images are saved as WebP if Pillow is installed, otherwise PNG.

The node ids below were read from the file "78 Tarot Cards (Community)":
https://www.figma.com/design/DbqVqq6vUDQHS4LcPlgb29/78-Tarot-Cards--Community-
(the Major Arcana layers are named 0..39 in Figma, so names here come from their position).
"""

import argparse
import io
import json
import os
import urllib.request
from pathlib import Path

FILE_KEY = "DbqVqq6vUDQHS4LcPlgb29"
OUT = Path(__file__).resolve().parent.parent / "static" / "tarot"

MAJOR = ["The Fool", "The Magician", "The High Priestess", "The Empress", "The Emperor",
         "The Hierophant", "The Lovers", "The Chariot", "Strength", "The Hermit",
         "Wheel of Fortune", "Justice", "The Hanged Man", "Death", "Temperance",
         "The Devil", "The Tower", "The Star", "The Moon", "The Sun", "Judgement", "The World"]
RANKS = ["Ace", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten",
         "King", "Knight", "Page", "Queen"]  # the order the layers appear in each suit section
SUIT_FIRST_NODE = {"Wands": 27, "Cups": 42, "Swords": 58, "Pentacles": 73}


def card_nodes() -> dict[str, str]:
    """node id -> file name (without extension)."""
    nodes = {f"1:{3 + i}": f"{i:02d} {name}" for i, name in enumerate(MAJOR)}
    for suit, first in SUIT_FIRST_NODE.items():
        for i, rank in enumerate(RANKS):
            nodes[f"1:{first + i}"] = f"{suit} - {rank} of {suit}"
    return nodes


def api_get(url: str, token: str) -> dict:
    request = urllib.request.Request(url, headers={"X-Figma-Token": token})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def save(data: bytes, stem: str):
    try:
        from PIL import Image
        Image.open(io.BytesIO(data)).save(OUT / f"{stem}.webp", "WEBP", quality=88, method=6)
    except ImportError:
        (OUT / f"{stem}.png").write_bytes(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--token", default=os.getenv("FIGMA_TOKEN"), help="Figma personal access token")
    parser.add_argument("--file", default=FILE_KEY, help="Figma file key (your copy of the deck)")
    parser.add_argument("--scale", type=float, default=1.0, help="1 = 500 x 836 px for Major Arcana")
    parser.add_argument("--all", action="store_true", help="export again even if the file exists")
    args = parser.parse_args()
    if not args.token:
        parser.error("give --token or set FIGMA_TOKEN")

    OUT.mkdir(parents=True, exist_ok=True)
    existing = {p.stem for p in OUT.iterdir()}
    todo = {n: s for n, s in card_nodes().items() if args.all or s not in existing}
    print(f"{78 - len(todo)} cards already present, exporting {len(todo)}")

    ids = list(todo)
    for start in range(0, len(ids), 20):           # the API accepts many ids per request
        batch = ids[start:start + 20]
        url = (f"https://api.figma.com/v1/images/{args.file}"
               f"?ids={','.join(batch)}&format=png&scale={args.scale}")
        images = api_get(url, args.token).get("images", {})
        for node in batch:
            link = images.get(node)
            if not link:
                print(f"  ! no image for {node} ({todo[node]})")
                continue
            with urllib.request.urlopen(link, timeout=60) as response:
                save(response.read(), todo[node])
            print(f"  saved {todo[node]}")
    print(f"Done. Reload the page: the deck in {OUT} now has all its cards.")


if __name__ == "__main__":
    main()
