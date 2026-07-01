# Aura Assist

A personal accessibility + knowledge agent for people with chronic migraines.

Built as a real, fully-completed follow-on to CodePath AI201-style projects —
same spirit (RAG pipelines, small Flask/Gradio apps) but meant to actually be
used, not just submitted.

## What it does

Three modules, one app:

1. **Accessible reader** — takes a PDF and re-renders it as reflowable,
   theme-adjustable text (background color, text color, font size) so it's
   comfortable to read during light sensitivity or migraine aura.
2. **Math-to-speech normalizer** — takes a PDF with math notation and
   rewrites the equations as naturally spoken English (with punctuation-based
   pacing and explicit handling of parenthetical scope), exported in a format
   ready to drop into Speechify.
3. **Migraine knowledge agent** — a RAG agent grounded in migraine clinical
   guidelines (ICHD-3, AHS/AAN) and open-access literature. Informational
   only — not a substitute for a clinician, and it escalates rather than
   answers when it sees red-flag symptoms.

## Status

🚧 Early build. Module A (accessible reader) is the current focus.

## Setup

```bash
python -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
python app.py
```

## Project structure

See `PROJECT.md` for the architecture writeup and design decisions.
