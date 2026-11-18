#!/usr/bin/env python3
"""
Download the page's Google Fonts into static/fonts/ so the interface works offline.

  python scripts/get_fonts.py

Fonts (all SIL Open Font License):
  Pinyon Script        Victorian copperplate titles
  Cormorant SC         small-caps labels
  Cormorant Garamond   reading text (supports Vietnamese)
"""

import re
import urllib.request
from pathlib import Path

CSS_URL = ("https://fonts.googleapis.com/css2?family=Pinyon+Script"
           "&family=Cormorant+SC:wght@500;600"
           "&family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&display=swap")
# A modern browser user agent makes Google serve compact woff2 files.
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
OUT = Path(__file__).resolve().parent.parent / "static" / "fonts"


def get(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    css = get(CSS_URL).decode("utf-8")
    urls = sorted(set(re.findall(r"url\((https://[^)]+)\)", css)))
    print(f"Downloading {len(urls)} font files to {OUT}")
    for i, url in enumerate(urls):
        name = f"gf-{i:02d}.woff2"
        (OUT / name).write_bytes(get(url))
        css = css.replace(url, name)
    (OUT / "fonts.css").write_text("/* Downloaded by scripts/get_fonts.py */\n" + css, encoding="utf-8")
    print("Done. static/fonts/fonts.css now points to the local copies.")


if __name__ == "__main__":
    main()
