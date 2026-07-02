"""
Manual integration test: Module A + Module B together, on a real PDF.

NOT part of the automated test suite — makes real (billed, if any pages
need fallback) API calls and writes a file for you to actually open and
read, rather than asserting anything.

What this does:
1. Extract the PDF page-by-page with Module B (src/math_speech.py),
   flagging + correcting any pages whose text layer can't be trusted
2. Join all pages into one document
3. Render it through Module A's theming (src/accessible_reader.py)
4. Write the result to a real HTML file you can open in a browser

Usage:
    python tests/manual_test_reading_session.py data/samples/attention.pdf
    python tests/manual_test_reading_session.py data/samples/IsoMap.pdf
"""

import os
import sys

from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.accessible_reader import render_accessible_html
from src.math_speech import extract_with_fallback_flags, resolve_fallback_pages

load_dotenv()

if len(sys.argv) != 2:
    print("Usage: python tests/manual_test_reading_session.py <path_to_pdf>")
    sys.exit(1)

pdf_path = sys.argv[1]
if not os.path.exists(pdf_path):
    print(f"File not found: {pdf_path}")
    sys.exit(1)

print(f"Extracting {pdf_path}...")
results = extract_with_fallback_flags(pdf_path)

flagged = [r for r in results if r["needs_fallback"]]
print(f"{len(flagged)}/{len(results)} pages need the vision fallback.")

if flagged:
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY not set — check your .env file.")
        sys.exit(1)
    print(f"Resolving {len(flagged)} flagged page(s) via vision (small real cost)...")
    results = resolve_fallback_pages(pdf_path, results)
else:
    print("No pages flagged — skipping vision calls entirely, no cost incurred.")

full_text = "\n\n".join(r["text"] for r in results)

print("Rendering through Module A's theming (soft_charcoal)...")
html = render_accessible_html(full_text, theme="soft_charcoal")

output_path = os.path.join(
    os.path.dirname(__file__), "..", "reading_session_output.html"
)
with open(output_path, "w", encoding="utf-8") as f:
    # wrap in a real standalone document this time — this file IS meant
    # to be opened directly in a browser, unlike the Gradio HTML fragment
    f.write(f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
             f"<title>Reading session</title></head><body>{html}</body></html>")

print(f"\nDone. Open this file in your browser:\n  {os.path.abspath(output_path)}")