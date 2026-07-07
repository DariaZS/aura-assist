# Aura Assist

A personal accessibility + knowledge agent for people with chronic migraines.

Built as a real, fully-completed follow-on to CodePath AI201-style projects —
same spirit (RAG pipelines, small Flask/Gradio apps) but meant to actually be
used, not just submitted.

## What it does

Three modules:

1. **Accessible reader** — two ways to make a PDF comfortable to read during
   light sensitivity or migraine aura:
   - *Whole-PDF recolor:* keeps the entire document exactly as laid out
     (figures, math, tables, columns all intact) and only remaps the colors —
     dark background, warm light text, softened graphs. Best for reading a
     book or paper whole while glancing at math/figures in their original
     form. No internet or API needed; runs fully offline.
   - *Text reflow:* extracts the text and re-renders it as reflowable,
     theme-adjustable HTML (background color, text color, font size).
2. **Math-to-speech normalizer** — takes a PDF with math notation and rewrites
   the equations as naturally spoken English, exported ready to drop into
   Speechify. Handles broken/legacy PDF encodings by falling back to reading
   pages as images. *(In progress — extraction + vision fallback + math
   detection done; spoken-math rewrite next.)*
3. **Migraine knowledge agent** — a RAG agent grounded in migraine clinical
   guidelines (ICHD-3, AHS/AAN) and open-access literature. Informational
   only — not a substitute for a clinician, and it escalates rather than
   answers when it sees red-flag symptoms. *(Not started yet.)*

## Status

🚧 Active build.
- **Module A — accessible reader:** working. Whole-PDF recolor and text
  reflow both functional.
- **Module B — math-to-speech:** in progress. PDF extraction, image/vision
  fallback for broken math encodings, and math-span detection are done and
  tested; the spoken-math rewrite and `.txt` export are next.
- **Module C — migraine knowledge agent:** not started.

## Setup

```bash
python -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env            # then add your ANTHROPIC_API_KEY for Module B
```

## Usage

**Recolor a whole PDF to the dark charcoal theme** (offline, no API cost):

```bash
python recolor_book.py path/to/book.pdf
python recolor_book.py path/to/book.pdf --scale 3   # sharper, larger file
```

Writes `<name>_charcoal.pdf` alongside the input. Note: the output is page
images, so the text isn't selectable — for audio, highlight from the original
PDF and use the recolored one for comfortable viewing.

**Text-reflow reader (Gradio demo):**

```bash
python demo.py       # then open http://localhost:7860
```

## Known limitations

- Recolored PDFs are images, so their text isn't selectable/searchable.
- Figures/graphs in the math-to-speech pipeline are skipped (extraction
  drops vector graphics); only their captions come through.
- Math on cleanly-extracted pages can arrive spatially fragmented; those
  pages are routed through the image/vision path instead.

## Project structure

See `PLANNING.md` for the architecture writeup, design decisions, and the
running history of what's been built and why.