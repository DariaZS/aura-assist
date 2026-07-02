"""
Module B: math span detection

Given clean-extracted text (a page that did NOT need the vision fallback),
find the spans that are actually mathematical notation, so only those get
sent through the spoken-math rewrite later — not the whole document.

This is a REGEX/HEURISTIC first pass, deliberately. The goal isn't perfect
classification; it's to cheaply flag "this looks like math" so we spend
LLM calls only where they're needed. We tune it against real extracted
text and see how far it gets before reaching for anything smarter.

What counts as a math span here (based on real patterns seen in the
Attention paper and Isomap paper):
- Unicode math symbols: √ Σ ∫ ∇ ∈ ≤ ≥ ≠ ± × ÷ ∞ ∂ ∀ ∃ and Greek letters
- Subscript/superscript notation written inline: d_k, x_i, QK^T, n^2
- Standalone numbered equations: a line ending in "(1)", "(2)", etc.
- Operator-dense fragments: things like "softmax(QK^T / √d_k)V"

What we deliberately DON'T try to catch yet:
- Plain-prose numbers ("28.4 BLEU", "8 GPUs") — not math notation, just data
- Inline single letters that might be variables ("the value d") — too
  ambiguous for regex; a later LLM pass can judge these in context
"""

import re

# Unicode symbols that almost always indicate real math when present.
# Calibrated against real extracted text from the Attention + Isomap
# papers — these are the symbols that actually survive extraction as
# correct Unicode and reliably signal math (NOT the underscore, which in
# practice only appeared in variable *names* like "warmup_steps").
MATH_SYMBOLS = "√∑Σ∫∇∈∉≤≥≠≈±×÷·∞∂∀∃⊂⊆∪∩→←↔⇒⇐⇔∝∅ℝℕℤℚ−"

# Greek letters (lower and upper) commonly used as math variables.
GREEK = (
    "αβγδεζηθικλμνξοπρστυφχψω"
    "ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ"
)

# Compiled patterns, each a signal that a span contains math.
_PATTERNS = [
    # any hard math symbol
    re.compile(f"[{re.escape(MATH_SYMBOLS)}]"),
    # any Greek letter
    re.compile(f"[{GREEK}]"),
    # subscript/superscript notation: letter or paren followed by _ or ^
    # then an alphanumeric or brace group — e.g. d_k, x_i, QK^T, n^2, d_{k}
    re.compile(r"[A-Za-z0-9)\]]\s*[_^]\s*[{(]?[A-Za-z0-9]"),
    # a standalone equation number at end of a line: "... (1)" / "... (12)"
    re.compile(r"\(\d{1,3}\)\s*$"),
]


def line_is_math(line: str) -> bool:
    """Heuristic: does this single line contain mathematical notation?"""
    if not line.strip():
        return False
    return any(p.search(line) for p in _PATTERNS)


def find_math_spans(text: str) -> list[dict]:
    """Scan text line-by-line and return the spans that look like math.

    Returns a list of dicts:
        [{"line_number": 3, "text": "Attention(Q,K,V) = softmax(...)"}, ...]

    Line-based (rather than character-offset) because the downstream
    rewrite works on readable chunks, and because extracted PDF text is
    already broken into lines in a way that roughly follows the document.
    """
    spans = []
    for i, line in enumerate(text.split("\n")):
        if line_is_math(line):
            spans.append({"line_number": i, "text": line.strip()})
    return spans