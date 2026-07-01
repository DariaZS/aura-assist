# Planning

Living doc for what's built, what's next, and the reasoning behind design
choices. Update this as things change — it's meant to stay current, not be
a one-time writeup.

## Module A — Accessible reader

**Status: working.**

- PDF → text extraction (PyMuPDF)
- Themed HTML output (sepia / dark / high_contrast / soft_charcoal)
- Baskerville font, serif fallbacks
- Flask API (`app.py`) + separate Gradio demo (`demo.py`) — kept separate
  because Flask (WSGI) and `gr.mount_gradio_app` (needs ASGI) don't mount
  together directly

**Known bugs fixed along the way** (kept here to not repeat them later):
- Gradio's `HTML` component inserts a *fragment*, not a document — styles
  on `<html>`/`<body>` get silently stripped. Fix: style a plain `<div>`.
- Gradio's own theme CSS overrides text color with `!important`. Fix: add
  `!important` to our inline styles too, on both the container and each
  `<p>` (inheritance loses to any rule that directly targets a child).

**Open / not yet done:**
- [ ] Structure detection — headings vs. body text currently render
      identically; PDF font-size/weight metadata could distinguish them
- [ ] Live custom color picker in the UI, instead of only fixed presets
- [ ] Optional: export the themed version back to PDF (WeasyPrint), not
      just HTML, for people who want a file rather than a browser tab

## Module B — Math-to-speech normalizer

**Status: starting now.**

**Goal:** take a PDF containing math notation and produce text that reads
naturally out loud when imported into Speechify — equations verbalized,
punctuation doing the work of pacing (since Speechify has no SSML/pause
tags), and parenthetical scope narrated explicitly rather than left to be
inferred from symbols alone.

**Pipeline:**
1. Extract text preserving reading order (reuse/extend Module A's
   extraction — may need pdfplumber instead of/alongside PyMuPDF if we
   need font metadata to spot subscripts/superscripts)
2. Detect math spans — regex + heuristics for symbols (∑, ∫, √, etc.) and
   sub/superscript patterns
3. Send math spans (not the whole document) to an LLM with a system
   prompt specialized for spoken-math rewriting
4. Reassemble into full text, with punctuation engineered for pacing
5. Export as `.txt` or `.docx` — whichever imports into Speechify more
   cleanly (needs a quick test)

**Decisions still open:**
- [ ] Which LLM — Groq (matches your AI201 RAG stack, fast/cheap) or
      Claude API (likely better at nuanced math phrasing)? Worth testing
      both on a few tricky equations before committing.
- [ ] Math detection: regex-first, or hand off ambiguous spans to the LLM
      to decide "is this math or just symbols in prose"?
- [ ] `.txt` vs `.docx` output — test which Speechify import behaves
      better with punctuation-based pausing preserved

**Build order (small commits, same pattern as Module A):**
1. Extraction reused from Module A, confirmed it preserves reading order
2. Math span detection (regex heuristics), unit-tested on sample equations
3. LLM rewrite call + prompt, tested on isolated spans first
4. Reassembly into full punctuated text
5. Export to file, manually tested by importing into Speechify
6. Wire into `demo.py` as a second tab

## Module C — Migraine knowledge agent (RAG)

**Status: not started.**

- Corpus: ICHD-3 diagnostic criteria, AHS/AAN clinical guidelines,
  open-access review articles — no scraped textbooks
- ChromaDB + embeddings, Groq/Claude for generation (same shape as the
  TakeMeter/RAG AI201 projects)
- Safety-first system prompt: general education only, never dosing or
  diagnosis, always defers to a clinician
- Hard-coded red-flag detection (thunderclap headache, neuro deficits,
  fever + stiff neck, etc.) that escalates to "seek emergency care" rather
  than answering from the RAG pipeline

## Commit conventions

Following the pattern from Modules A/B:
- `feat:` new capability
- `fix:` bug fix
- `chore:` scaffolding, deps, config
- `docs:` writeups like this one
- `test:` tests

Small commits, one logical change each — easier to trace back through
later than one big dump.