"""
Recolor a whole PDF to the charcoal dark theme, preserving all layout,
figures, math, and tables — only the colors change.

Usage:
    python recolor_book.py path/to/book.pdf
    python recolor_book.py path/to/book.pdf path/to/output.pdf

If no output path is given, writes alongside the input as
"<name>_charcoal.pdf".

Note: this renders every page to an image, so it can be slow and produce
a large file for a big textbook. Run it once per book. Higher --scale is
sharper but bigger; 2.0 is a good default for reading.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from src.recolor_pdf import recolor_pdf

if len(sys.argv) < 2:
    print("Usage: python recolor_book.py <input.pdf> [output.pdf] [--scale N]")
    print("  --scale N : render resolution (default 2.0). Higher = sharper,")
    print("              less grainy, but larger file & slower. Try 3 or 4")
    print("              for a paper; keep at 2 for a big textbook.")
    sys.exit(1)

# Pull out --scale if present, so it can go anywhere in the args.
scale = 2.0
args = sys.argv[1:]
if "--scale" in args:
    idx = args.index("--scale")
    try:
        scale = float(args[idx + 1])
        del args[idx:idx + 2]
    except (IndexError, ValueError):
        print("--scale needs a number, e.g. --scale 3")
        sys.exit(1)

input_path = args[0]
if not os.path.exists(input_path):
    print(f"File not found: {input_path}")
    sys.exit(1)

if len(args) >= 2:
    output_path = args[1]
else:
    base, _ = os.path.splitext(input_path)
    output_path = f"{base}_charcoal.pdf"

print(f"Recoloring {input_path} -> {output_path}  (scale={scale})")
print("(rendering every page — this can take a while for a big book)\n")

recolor_pdf(input_path, output_path, scale=scale)

size_mb = os.path.getsize(output_path) / 1024 / 1024
print(f"\nDone. {size_mb:.1f} MB written to:\n  {os.path.abspath(output_path)}")


