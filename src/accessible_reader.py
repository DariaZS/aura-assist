"""
Module A: Accessible Reader

Takes a PDF and re-renders its text content as theme-adjustable HTML —
custom background color, text color, and font size — so it's comfortable
to read during light sensitivity or migraine aura.

Why HTML instead of editing the PDF directly: PDFs are fixed-layout, so
recoloring in place is fragile and doesn't reflow. Extracting the text and
rendering it as HTML gives true control over theme, and plays nicely with
tools like DarkReader.

Currently: plain text extraction + basic theming. Structure (headings,
paragraphs) detection comes next.
"""

import fitz  # PyMuPDF

# A few starter presets. Feel free to add more once you see it running.
THEMES = {
    "sepia": {"bg": "#f4ecd8", "text": "#2c2b2a", "font_size": "18px"},
    "dark": {"bg": "#1b1b1b", "text": "#e0e0e0", "font_size": "18px"},
    "high_contrast": {"bg": "#000000", "text": "#ffffff", "font_size": "20px"},
    "soft_charcoal": {"bg": "#2c2c2b", "text": "#d8d5cc", "font_size": "18px"},
}


def extract_text(pdf_path: str) -> str:
    """Pull raw text out of a PDF, page by page."""
    doc = fitz.open(pdf_path)
    pages = [page.get_text() for page in doc]
    doc.close()
    return "\n\n".join(pages)


def render_accessible_html(
    text: str,
    theme: str = "sepia",
    custom_bg: str | None = None,
    custom_text: str | None = None,
    custom_font_size: str | None = None,
) -> str:
    """Wrap extracted text in themed HTML.

    Pass custom_bg / custom_text / custom_font_size to override a preset
    theme's individual values.
    """
    preset = THEMES.get(theme, THEMES["sepia"])
    bg = custom_bg or preset["bg"]
    color = custom_text or preset["text"]
    font_size = custom_font_size or preset["font_size"]

    # Preserve paragraph breaks; escape nothing fancy yet — plain text only.
    paragraphs = "".join(
        f'<p style="color:{color} !important; margin:0 0 1em 0;">{p}</p>'
        for p in text.split("\n\n") if p.strip()
    )

    return f"""
    <div style="background-color:{bg} !important; color:{color} !important;
                font-size:{font_size} !important;
                font-family: Baskerville, 'Libre Baskerville', Garamond, Georgia, serif;
                line-height:1.6; padding:2rem; max-width:700px; margin:auto;
                border-radius:8px;">
        {paragraphs}
    </div>
    """


def process_pdf(pdf_path: str, theme: str = "sepia") -> str:
    """End-to-end: PDF path in, themed HTML string out."""
    text = extract_text(pdf_path)
    return render_accessible_html(text, theme=theme)