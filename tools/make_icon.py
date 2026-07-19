"""Build ``assets/hyprop.ico`` from the MELprop logo PNG.

Windows shortcuts need a multi-resolution ``.ico``; Explorer picks the size it
needs (16 px in lists, 256 px in large-icon view). Scaling one bitmap at run
time gives a blurry result, so every standard size is embedded up front.

Usage::

    .venv\\Scripts\\python tools/make_icon.py [source.png]

Default source: ``assets/melprop_logo.png``.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]

#: Margin kept around the trimmed artwork, as a fraction of the icon edge.
#: Windows renders shortcut icons edge-to-edge, so a small inset stops the
#: leaves from touching the tile border.
PADDING = 0.06


def build(src: Path, dst: Path) -> Path:
    """Trim, square and export *src* as a multi-size ICO at *dst*."""
    img = Image.open(src).convert("RGBA")

    # The logo is supplied on an opaque dark background; drop that background so
    # the icon blends with any Windows theme. Pixels close to the corner colour
    # (sampled at 0,0) become transparent.
    bg = img.getpixel((0, 0))[:3]
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2]) < 40:
                px[x, y] = (r, g, b, 0)

    bbox = img.getbbox()
    if bbox is not None:
        img = img.crop(bbox)

    side = max(img.size)
    canvas_side = int(side / (1 - 2 * PADDING))
    canvas = Image.new("RGBA", (canvas_side, canvas_side), (0, 0, 0, 0))
    canvas.paste(
        img,
        ((canvas_side - img.width) // 2, (canvas_side - img.height) // 2),
        img,
    )

    dst.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(dst, format="ICO", sizes=SIZES)
    return dst


def main() -> int:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else ASSETS / "melprop_logo.png"
    if not src.is_file():
        print(f"Nie znaleziono pliku zrodlowego: {src}")
        print("Zapisz logo jako assets/melprop_logo.png i uruchom ponownie.")
        return 1
    out = build(src, ASSETS / "hyprop.ico")
    print(f"OK: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
