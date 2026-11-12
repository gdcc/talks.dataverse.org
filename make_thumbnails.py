#!/usr/bin/env python3
"""Make a small image of the first slide of each cached slide deck.

Reads slide files from cache/<source>/<name>.<ext> (cache/ is gitignored) and
writes thumbs/<source>/<name>.webp, 560 pixels wide. Thumbnails that already
exist at this width are skipped, so it's cheap to run again after adding
slides to the cache; changing WIDTH remakes them all.

Usage:
    python3 make_thumbnails.py
    python3 talks_from_raw.py > talks.json

Needs pdftoppm (Poppler) for PDFs and Pillow. PowerPoint files are rendered
with macOS Quick Look (qlmanage).
"""

import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

WIDTH = 560  # shown at about 280 px wide, so sharp on high-resolution screens
QUALITY = 60  # WebP quality; about 12 KB per thumbnail
CACHE = Path("cache")
THUMBS = Path("thumbs")


def render(src, png_dir):
    """Render the first page of src to a PNG in png_dir and return its path."""
    if src.suffix == ".pdf":
        out = png_dir / "page"
        subprocess.run(
            ["pdftoppm", "-f", "1", "-l", "1", "-png", "-scale-to-x", str(WIDTH * 2),
             "-scale-to-y", "-1", "-singlefile", str(src), str(out)],
            check=True, capture_output=True, timeout=120)
        return out.with_suffix(".png")
    if src.suffix in (".pptx", ".ppt", ".key", ".odp"):
        subprocess.run(["qlmanage", "-t", "-s", str(WIDTH * 2), "-o", str(png_dir), str(src)],
                       check=True, capture_output=True, timeout=120)
        return png_dir / (src.name + ".png")
    raise ValueError(f"don't know how to render {src.suffix}")


def main():
    made, skipped, failed = 0, 0, []
    for src in sorted(CACHE.glob("*/*")):
        dest = THUMBS / src.parent.name / (src.stem + ".webp")
        # Keep an existing thumbnail unless WIDTH has changed since it was made.
        if dest.exists() and Image.open(dest).width == WIDTH:
            skipped += 1
            continue
        try:
            with tempfile.TemporaryDirectory() as tmp:
                png = render(src, Path(tmp))
                img = Image.open(png).convert("RGB")
                img.thumbnail((WIDTH, WIDTH * 2))
                dest.parent.mkdir(parents=True, exist_ok=True)
                img.save(dest, "WEBP", quality=QUALITY, method=6)
            made += 1
        except Exception as e:
            failed.append(f"{src}: {e}")
    print(f"{made} made, {skipped} already there, {len(failed)} failed")
    for f in failed:
        print("  " + f, file=sys.stderr)


if __name__ == "__main__":
    main()
