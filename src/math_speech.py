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

import base64
import io

import pdfplumber

# Font-family name fragments we've confirmed produce silently-wrong math
# text. This list grows as we encounter more legacy-encoded PDFs — it's
# not exhaustive, just what we've verified so far.
KNOWN_BROKEN_MATH_FONTS = (
    "MathPi",
    "GreekwithMathPi",
    "MathematicalPi",
)

# Model used for the vision fallback. Sonnet is capable enough for careful
# transcription and far cheaper than reaching for Opus on every flagged page.
VISION_MODEL = "claude-sonnet-5"

TRANSCRIBE_PROMPT = """\
Transcribe the text on this page exactly as written. This is a page from
an academic paper whose PDF text layer is unreliable for mathematical
notation, so we're reading the image directly instead.

Rules:
- Transcribe faithfully — do not solve, simplify, or explain the math,
  just write down exactly what's on the page.
- Render every mathematical symbol using standard Unicode characters
  where possible (Greek letters like τ, ε, Σ, Δ; operators like √, ≤, ∇;
  etc.) rather than describing them in words.
- Write subscripts and superscripts inline using ^ and _ (e.g. x_i, d^2)
  since Unicode sub/superscripts don't cover every character we need.
- Preserve paragraph and equation structure as it appears on the page.
- Output only the transcribed text — no preamble, no commentary, no
  markdown formatting or code fences.
"""


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


def render_page_as_png(pdf_path: str, page_number: int, resolution: int = 150) -> bytes:
    """Render a single PDF page (1-indexed) as PNG bytes."""
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_number - 1]
        image = page.to_image(resolution=resolution)
        buf = io.BytesIO()
        image.original.save(buf, format="PNG")
        return buf.getvalue()


def transcribe_page_with_vision(image_bytes: bytes, model: str = VISION_MODEL) -> str:
    """Send a page image to Claude and get back a faithful text
    transcription, used when the PDF's own text layer can't be trusted.

    Requires ANTHROPIC_API_KEY to be set (read automatically from the
    environment by the anthropic client — make sure your .env is loaded,
    e.g. via `from dotenv import load_dotenv; load_dotenv()` at your
    app's entry point).
    """
    import anthropic  # imported here, not at module level, so the rest of

    # this module (rendering, detection) stays testable without the SDK

    client = anthropic.Anthropic()
    b64_image = base64.standard_b64encode(image_bytes).decode("utf-8")

    response = client.messages.create(
        model=model,
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": b64_image,
                        },
                    },
                    {"type": "text", "text": TRANSCRIBE_PROMPT},
                ],
            }
        ],
    )
    return response.content[0].text


def resolve_fallback_pages(pdf_path: str, results: list[dict]) -> list[dict]:
    """Given the output of extract_with_fallback_flags(), replace the
    text of any flagged page with a vision-transcribed version. This is
    the only function in this module that actually calls the API —
    everything upstream is free, local, and instant.

    Mutates and returns the same list. Adds a "source" key to each dict
    so we can tell which pages came from the text layer vs. vision.
    """
    for r in results:
        if r["needs_fallback"]:
            image_bytes = render_page_as_png(pdf_path, r["page"])
            r["text"] = transcribe_page_with_vision(image_bytes)
            r["source"] = "vision"
        else:
            r["source"] = "text_layer"
    return results


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