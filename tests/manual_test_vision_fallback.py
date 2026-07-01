"""
Manual test for the vision fallback — NOT part of the automated test
suite, since it makes a real (billed) API call.

Run this once by hand to confirm transcribe_page_with_vision() actually
recovers the correct equation from the Isomap PDF's broken page 2.
Compare the output against the real equation:

    E = ||τ(D_G) - τ(D_Y)||_L2

Usage:
    python tests/manual_test_vision_fallback.py
"""

import os
import sys

from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.math_speech import render_page_as_png, transcribe_page_with_vision

load_dotenv()

if not os.getenv("ANTHROPIC_API_KEY"):
    print("ANTHROPIC_API_KEY not set — check your .env file.")
    sys.exit(1)

pdf_path = os.path.join(
    os.path.dirname(__file__), "..", "data", "samples", "IsoMap.pdf"
)

if not os.path.exists(pdf_path):
    print(f"Sample PDF not found at {pdf_path} — put IsoMap.pdf in data/samples/")
    sys.exit(1)

print("Rendering page 2 as an image...")
image_bytes = render_page_as_png(pdf_path, page_number=2)
print(f"  {len(image_bytes)} bytes")

print("\nSending to Claude for transcription (this costs a small amount)...")
result = transcribe_page_with_vision(image_bytes)

print("\n--- Transcribed text ---")
print(result)
print("--- end ---")

print("\nManually check: does this contain something close to")
print('  E = ||τ(D_G) - τ(D_Y)||_L2')
print("with correct τ, Σ, √ symbols rather than t, S, = ?")