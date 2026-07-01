"""
Module B: Math-to-speech normalizer — extraction stage

Step 1 of the pipeline: extract text per-page with pdfplumber, and flag
pages where the text extraction is likely unreliable so they can be
re-read as images instead of trusted as-is.

Two known failure modes, two narrow detectors (see PLANNING.md for the
research behind these):

1. Unmapped glyphs — pdfplumber emits literal "(cid:NN)" strings when a
   font's ToUnicode CMap doesn't cover a glyph it needs to render. This is
   an honest failure, easy to detect. Modern arXiv-style PDFs hit this
   occasionally (confirmed on "Attention Is All You Need").

2. Broken legacy math fonts — some pre-2000s PDFs (this project's
   original test case: Tenenbaum et al.'s Isomap paper, Science 2000)
   used custom PostScript math fonts with no working Unicode mapping at
   all. Extraction doesn't error out — it silently returns the WRONG
   character (ε→e, τ→t, Σ→S, √→=, consistently but incorrectly). There's
   no reliable way to catch this from the text alone; what we CAN detect
   is the presence of the offending font family itself.
"""

import pdfplumber

# Font-family name fragments we've confirmed produce silently-wrong math
# text. This list grows as we encounter more legacy-encoded PDFs — it's
# not exhaustive, just what we've verified so far.
KNOWN_BROKEN_MATH_FONTS = (
    "MathPi",
    "GreekwithMathPi",
    "MathematicalPi",
)


def page_needs_image_fallback(page) -> tuple[bool, str]:
    """Check a single pdfplumber page for signs its text layer can't be
    trusted. Returns (needs_fallback, reason)."""
    text = page.extract_text() or ""

    if "(cid:" in text:
        return True, "unmapped glyph — (cid:) artifact found"

    fonts_on_page = {c["fontname"] for c in page.chars}
    for font in fonts_on_page:
        if any(bad in font for bad in KNOWN_BROKEN_MATH_FONTS):
            return True, f"known-broken math font detected ({font})"

    return False, ""


def extract_with_fallback_flags(pdf_path: str) -> list[dict]:
    """Extract text page-by-page, flagging which pages need image fallback.

    Returns a list of dicts:
        [{"page": 1, "text": ..., "needs_fallback": False, "reason": ""}, ...]

    This does NOT perform the image fallback itself — that's the next
    build step, once the LLM vision call is wired up. This step only
    decides which pages would need it.
    """
    results = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            needs_fallback, reason = page_needs_image_fallback(page)
            results.append({
                "page": i,
                "text": page.extract_text() or "",
                "needs_fallback": needs_fallback,
                "reason": reason,
            })
    return results