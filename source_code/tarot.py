"""
Reads the tarot card images in static/tarot/ and puts them in deck order.

Card files can be named almost any way Figma exports them, for example
"The Fool.png", "00_the_fool.png", "Ace of Cups.png", "cups-01.png", "2 of Wands.png".
The name is matched to one of the 78 standard cards to get its title, numeral and
place in the deck. A file named "back" (or "card back") is used as the back of every card.
"""

import os
import re

MAJOR = [
    "The Fool", "The Magician", "The High Priestess", "The Empress", "The Emperor",
    "The Hierophant", "The Lovers", "The Chariot", "Strength", "The Hermit",
    "Wheel of Fortune", "Justice", "The Hanged Man", "Death", "Temperance",
    "The Devil", "The Tower", "The Star", "The Moon", "The Sun", "Judgement", "The World",
]
ROMAN = ["0", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII",
         "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX", "XXI"]
SUITS = ["wands", "cups", "swords", "pentacles"]
RANKS = ["Ace", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten",
         "Page", "Knight", "Queen", "King"]
RANK_WORDS = {r.lower(): i for i, r in enumerate(RANKS)} | {"one": 0}
TYPES = (".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif")


def _words(stem: str) -> list[str]:
    return re.findall(r"[a-z]+|\d+", stem.lower())


def identify(stem: str):
    """Returns (order, numeral, title) or None if the name is not a standard card."""
    words = _words(stem)
    text = " ".join(w for w in words if not w.isdigit())

    suit = next((s for s in SUITS if s in words), None)
    if suit is None and "coins" in words:
        suit = "pentacles"
    if suit:
        rank = next((RANK_WORDS[w] for w in words if w in RANK_WORDS), None)
        if rank is None:
            digits = [int(w) for w in words if w.isdigit() and 1 <= int(w) <= 14]
            rank = digits[0] - 1 if digits else None
        if rank is not None:
            order = 22 + SUITS.index(suit) * 14 + rank
            return order, "", f"{RANKS[rank]} of {suit.title()}"

    for i, name in enumerate(MAJOR):
        key = name.lower().replace("the ", "")
        if key in text or (key == "judgement" and "judgment" in text):
            return i, ROMAN[i], name
    # a bare number 0-21 is read as a Major Arcana card
    if words and words[0].isdigit() and int(words[0]) <= 21 and not text:
        n = int(words[0])
        return n, ROMAN[n], MAJOR[n]
    return None


def load_deck(folder: str) -> dict:
    cards, back = [], None
    if not os.path.isdir(folder):
        return {"cards": [], "back": None}
    for file in sorted(os.listdir(folder)):
        stem, ext = os.path.splitext(file)
        if ext.lower() not in TYPES or file.startswith("."):
            continue
        url = f"/static/tarot/{file}"
        if re.fullmatch(r"(card[\s_-]*)?back([\s_-]*side)?", stem.lower()):
            back = url
            continue
        found = identify(stem)
        if found:
            order, numeral, title = found
        else:  # unknown name: keep it, at the end, titled from the file name
            order, numeral, title = 1000 + len(cards), "", re.sub(r"[_-]+", " ", stem).strip().title()
        cards.append({"id": file, "url": url, "order": order, "numeral": numeral, "name": title})
    cards.sort(key=lambda c: c["order"])
    return {"cards": cards, "back": back}
