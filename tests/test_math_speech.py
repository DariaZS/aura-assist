import os

import pytest

from src.math_speech import extract_with_fallback_flags

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "samples")
ISOMAP_PDF = os.path.join(SAMPLES_DIR, "IsoMap.pdf")
ATTENTION_PDF = os.path.join(SAMPLES_DIR, "attention.pdf")

# These sample PDFs are not committed to the repo (copyright), so tests
# skip gracefully if they're not present locally. Place them in
# data/samples/ to run these for real.
skip_if_missing = pytest.mark.skipif


@skip_if_missing(not os.path.exists(ISOMAP_PDF), reason="IsoMap.pdf not present locally")
def test_isomap_triggers_fallback():
    """Old paper with broken math font encoding should be flagged on at
    least the page containing the cost-function equation (page 2)."""
    results = extract_with_fallback_flags(ISOMAP_PDF)
    flagged = [r for r in results if r["needs_fallback"]]
    assert flagged, "Expected at least one page to need image fallback"
    # Page 2 (index 1) is where the τ(D_G) equation lives — this is the
    # specific page we manually confirmed has broken math font encoding.
    page_2 = results[1]
    assert page_2["needs_fallback"], (
        f"Expected page 2 to be flagged, got reason={page_2['reason']!r}"
    )


@skip_if_missing(not os.path.exists(ATTENTION_PDF), reason="attention.pdf not present locally")
def test_attention_paper_mostly_clean():
    """Modern LaTeX-generated paper should mostly NOT need fallback —
    a few rare (cid:) artifacts are fine, but most pages should extract
    cleanly since the underlying encoding is correct."""
    results = extract_with_fallback_flags(ATTENTION_PDF)
    flagged = [r for r in results if r["needs_fallback"]]
    assert len(flagged) < len(results) / 2, (
        f"Too many pages flagged ({len(flagged)}/{len(results)}) for a modern PDF"
    )


@skip_if_missing(not os.path.exists(ATTENTION_PDF), reason="attention.pdf not present locally")
def test_attention_paper_equation_text_correct():
    """Sanity check the actual content, not just the flag: the scaled
    dot-product attention equation should extract with real symbols."""
    results = extract_with_fallback_flags(ATTENTION_PDF)
    page_4_text = results[3]["text"]  # 0-indexed page 4 = list index 3
    assert "softmax" in page_4_text
    assert "QK" in page_4_text