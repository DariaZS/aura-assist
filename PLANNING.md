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

**Known bugs fixed along the way** (kept here so we don't repeat them):
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

**Extraction research (done):**

Tested `pdfplumber` against two real PDFs to understand what "extract math
from a PDF" actually runs into:

- **Old paper (Isomap, Tenenbaum et al., Science 2000):** math symbols
  extract as *silently wrong characters* — a broken/custom font encoding
  specific to that era's prepress typesetting. `ε`→`e`, `τ`→`t`, `Σ`→`S`,
  `√`→`=`, norm bars `‖ ‖`→`\`. Consistent substitution (same glyph always
  maps to same wrong character), but wrong regardless — and this is a
  property of the file itself, not something any extraction library can
  fix by trying harder. This affects old, pre-Unicode-era PDFs generally,
  not just this one paper.
- **Modern paper (Attention Is All You Need, arXiv 2017):** math extracts
  *correctly* — `Q`, `K`, `V`, `√`, `softmax` all come out as themselves.
  Confirms LaTeX/pdftex-generated PDFs (the overwhelming majority of
  modern ML papers — arXiv, NeurIPS, ICML) carry proper Unicode mappings.
  Two much smaller issues showed up instead, both tractable:
  - Missing spaces between words (`"Wecallourparticular"`) — a common,
    benign PDF-extraction quirk, fixable with extraction settings or a
    post-processing word-boundary heuristic.
  - Occasional `(cid:80)`-style strings — pdfplumber being honest about a
    glyph it couldn't map (vs. silently guessing wrong). This is
    detectable: a simple check for `(cid:` in extracted text tells us
    exactly when to fall back to reading that page as an image instead of
    trusting the text layer.

**Conclusion:** don't build a general OCR/image pipeline for everything —
build two narrow, targeted fallback triggers instead:
1. Page contains `(cid:` → unmapped glyph, re-read that page as an image
2. Page's extracted text is suspiciously dense with stray single-char
   symbols in positions where math is expected → likely old-encoding
   corruption, re-read as an image
Otherwise, trust the text extraction — it's correct for the papers this
tool will actually see most of the time.

**Image-fallback cost, if triggered:** roughly 1,000-2,000 tokens per
page image (~$0.002-0.004 at current Sonnet pricing) — cheap enough that
we don't need to be clever about minimizing how often it fires.

**Extraction code: built and tested (commit ready).**

`src/math_speech.py` implements `extract_with_fallback_flags()` — pdfplumber
extraction per page, with the two detectors above. Tested directly against
both sample PDFs (not committed to repo — copyright; kept locally in
`data/samples/`, gitignored):

- **IsoMap.pdf:** all 5 pages flagged. Page 2 (the cost-function equation)
  flagged via the `(cid:)` check — though on inspection, that particular
  hit was an unrelated curly-apostrophe glyph, not the equation itself.
  The font-name check independently confirmed the real issue: both
  `GreekwithMathPi` and `MathematicalPi-One` (the broken fonts) are
  present on that page. Both detectors fired, for different reasons —
  the page was correctly flagged either way.
- **attention.pdf:** 1/15 pages flagged (page 4), via `(cid:)` — and this
  time it's a genuine catch: the Σ in a footnote equation
  (`q·k = Σ qᵢkᵢ`) wasn't mapped by that font. Confirms the detector does
  real work on modern PDFs, not just accidental false positives.

**Honest caveat:** the `(cid:)` check isn't exclusively a math-symbol
detector — it also fires on unrelated typographic glyphs (curly quotes,
ligatures). That's fine for our purposes (falling back to an image on a
page that didn't strictly need it costs a fraction of a cent), but worth
remembering the *specific reason* a page gets flagged isn't always "this
page has a math problem."

Extraction and fallback execution both done — see the vision fallback
section above for how flagged pages actually get corrected.

**Image fallback: built and verified working (commit ready).**

`render_page_as_png()` and `transcribe_page_with_vision()` added to
`src/math_speech.py`. `anthropic` import is lazy (inside the function
that needs it), so the rest of the module stays testable without the SDK
installed. Manually tested end-to-end against the real broken equation
on IsoMap page 2:

| | Raw text extraction | Vision fallback |
|---|---|---|
| Equation | `E 5 \t~DG! 2 t~DY!\L2` | `E = ‖τ(D_G) − τ(D_Y)‖_L²` |
| Norm expansion | `=Si,j Aij 2` | `√(Σ_i,j A_ij²)` |

Every symbol recovered correctly — τ, ‖ ‖, √, Σ, subscripts, superscripts.
Confirms the two-tier design (trust text extraction by default, fall back
to vision only on flagged pages) works on the actual hardest case we have.

Model used: `claude-sonnet-5` (current mid-tier). Cost per fallback page:
roughly 1,500-2,500 tokens depending on image size — well under a cent.

**Integration testing found two more issues (both fixed):**

Running Module A + Module B together on the *full* Attention paper (not
just one page) surfaced problems invisible in isolated single-page tests:

1. **Missing spaces, pervasively** — `"Providedproperattributionis..."`
   throughout the whole document, not just the one line noticed earlier.
   Root cause: pdfplumber's default `x_tolerance` (character-adjacency
   threshold for word-splitting) was too loose for this PDF's font
   spacing. Fixed by setting `x_tolerance=1.5` in both extraction calls —
   confirmed this fixes spacing without breaking equation extraction
   (tested against the same softmax equation from before).

2. **Reversed/scrambled text on figure pages — a third failure mode our
   two detectors didn't catch.** Pages with the attention-visualization
   diagrams (vertical axis-label text) extracted as `"tI si ni siht
   tirips"` instead of "It is in this spirit" — word-by-word character
   reversal. Root cause: that text is rotated 90° in the PDF (axis
   labels), and naive extraction doesn't correctly reorder rotated
   glyphs. Diagnosed via pdfplumber's `upright` flag on each character —
   normal pages have 0-2% rotated characters, affected pages have
   45-60%+. Added a third detector: flag any page where >10% of
   characters are non-upright.

Detector count went from 1/15 pages flagged to 4/15 (the original page 4,
plus the three figure pages) once all three checks were in place —
meaning the earlier "1/15" result, while not wrong, was incomplete: it
just hadn't been tested against a full document with figure pages yet.

**Full-document integration test: verified working end-to-end.** Reran
against the complete Attention paper after both fixes — clean spacing
throughout, all three figure pages reading forward correctly, all
equations intact. Bonus: vision transcription also described diagram
structure for the architecture figures, not just text — useful for
accessibility beyond what was asked. Also fixed a response-parsing bug in
`transcribe_page_with_vision()` along the way: `response.content[0]`
isn't guaranteed to be the text block (a `ThinkingBlock` can come first);
fixed by filtering `response.content` by `block.type == "text"`.

**Pipeline:**
1. Extract text with pdfplumber (chosen over PyMuPDF for this module —
   exposes font metadata, needed for the `(cid:` detection above). Run the
   two fallback checks per page; re-read flagged pages as images via
   Claude's vision instead of trusting the text layer.
2. Detect math spans — regex + heuristics for symbols (∑, ∫, √, etc.) and
   sub/superscript patterns
3. Send math spans (not the whole document) to an LLM with a system
   prompt specialized for spoken-math rewriting
4. Reassemble into full text, with punctuation engineered for pacing
5. Export as `.txt` for now — `.pdf` export can come later as a polish
   step, once the core rewriting actually works

**Decisions still open:**
- [ ] Math detection: regex-first, or hand off ambiguous spans to the LLM
      to decide "is this math or just symbols in prose"?

**Decided:**
- LLM: Claude (`claude-sonnet-5`) — proven on the vision fallback, handles
  nuanced math/symbol transcription well. Not testing Groq separately for
  now given how well this worked; can revisit if cost ever becomes a
  real constraint (unlikely at this usage scale).
- Export format: `.txt` for now — simplest to build, and matches what
  Speechify actually needs. `.pdf` export is a nice-to-have for a later
  polish pass (needs a new dependency — WeasyPrint or reportlab — worth
  testing separately before relying on it)

**Build order (small commits, same pattern as Module A):**
1. ✅ pdfplumber extraction + fallback-trigger detection
2. ✅ Image rendering + vision transcription fallback, verified against
   the real broken equation
3. Math span detection (regex heuristics), unit-tested on sample equations
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

## Sharing (revisit later, not yet)

Once more of the app is built, decide how far to take this beyond
personal use. Options, roughly least → most effort:

1. **Gradio `share=True`** — one-line flag, temporary public URL
   (~72hrs). Good for showing a couple friends. Still runs on your
   machine, still uses your API key for every request they make — fine
   for light, short-term use only.
2. **Persistent demo (Hugging Face Spaces / Render)** — permanent URL,
   free tier available. Needs a real answer to "whose API key pays for
   this" — either a usage cap on your own key, or a "bring your own key"
   field in the UI.
3. **Open-source the repo** — zero hosting cost/risk to you; reaches only
   people comfortable setting up their own dev environment, which cuts
   against the accessibility goal somewhat.

**Things that stop being optional once it's not just you:**
- Module C's safety design (disclaimers, red-flag escalation) — matters
  much more with strangers describing real symptoms, not just personal use
- Privacy — be explicit that uploaded PDFs / health details aren't stored
  or logged beyond the session
- The tool's own accessibility (contrast, keyboard nav, screen-reader
  behavior) shouldn't only be tuned to one person's preferences

**Current plan:** don't decide yet. Once Module B is finished, a Tier 1
share (temporary link, one or two people) is enough for real feedback
without committing to hosting costs or a safety review before it's ready.

## Commit conventions

Following the pattern from Modules A/B:
- `feat:` new capability
- `fix:` bug fix
- `chore:` scaffolding, deps, config
- `docs:` writeups like this one
- `test:` tests

Small commits, one logical change each — easier to trace back through
later than one big dump.