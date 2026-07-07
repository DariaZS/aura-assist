"""
Module A (extension): whole-PDF recoloring

Different approach from the text-reflow reader. Instead of extracting text
and re-rendering it (which drops figures, fragments math, and flattens
tables), this keeps every page *whole* — it renders each page to an image
and remaps the colors: light background -> dark, dark text -> light.

This preserves the entire book exactly as laid out (figures, equations,
tables, columns) and only changes how it looks, which is ideal for reading
comfortably during light sensitivity while still being able to SEE the math,
code, and figures in their original form.

Trade-off vs. the reflow reader: the output is page images, so text isn't
selectable/reflowable and font size is fixed by the original layout. For
"read the whole book comfortably, highlight in a separate audio tool, glance
at the math," that trade-off is the right one.
"""

import io

import numpy as np
import pypdfium2 as pdfium
from PIL import Image

# Theme colors, matching the soft_charcoal reader theme.
# The page's luminance interpolates between these: originally-white areas
# become BG, originally-black areas become FG.
DEFAULT_BG = (0x1F, 0x1F, 0x1E)   # dark charcoal (was white background)
DEFAULT_FG = (0xD8, 0xD5, 0xCC)   # warm light (was black text)


def recolor_page_image(img: Image.Image, bg=DEFAULT_BG, fg=DEFAULT_FG) -> Image.Image:
    """Recolor a single rendered page image by luminance remapping.

    Bright pixels (page background) map toward `bg`; dark pixels (text,
    lines) map toward `fg`. Mid-tones (anti-aliasing, gray figures) land
    smoothly in between, which also softens bright graphs automatically.
    """
    arr = np.array(img.convert("RGB")).astype(np.float32)
    lum = (0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]) / 255.0

    bg_arr = np.array(bg, dtype=np.float32)
    fg_arr = np.array(fg, dtype=np.float32)

    out = np.empty_like(arr)
    for c in range(3):
        # lum=1 (white) -> bg, lum=0 (black) -> fg
        out[:, :, c] = lum * bg_arr[c] + (1.0 - lum) * fg_arr[c]

    return Image.fromarray(out.astype(np.uint8))


def recolor_pdf(
    pdf_path: str,
    output_path: str,
    bg=DEFAULT_BG,
    fg=DEFAULT_FG,
    scale: float = 2.0,
) -> str:
    """Recolor every page of a PDF and save the result as a new PDF.

    `scale` controls render resolution (2.0 ≈ 144 DPI, readable and not
    huge). Higher = sharper but larger file and slower.

    Returns the output path. This can be slow and memory-heavy for large
    books — it renders every page to an image — so it's meant to be run
    once per book, not interactively.
    """
    pdf = pdfium.PdfDocument(pdf_path)
    recolored_images = []

    n_pages = len(pdf)
    for i in range(n_pages):
        page = pdf[i]
        page_img = page.render(scale=scale).to_pil()
        recolored_images.append(recolor_page_image(page_img, bg=bg, fg=fg))
        print(f"  recolored page {i + 1}/{n_pages}")

    # Save all recolored page images into a single PDF.
    first, rest = recolored_images[0], recolored_images[1:]
    first.save(output_path, save_all=True, append_images=rest)
    return output_path