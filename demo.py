"""
Aura Assist — Gradio demo UI.

A quick visual front end for trying out Module A. Runs as its own process,
separate from the Flask API in app.py.

    python demo.py    -> http://localhost:7860
"""

import gradio as gr

from src.accessible_reader import THEMES, process_pdf


def gradio_accessible_reader(pdf_file, theme):
    if pdf_file is None:
        return "Upload a PDF to get started."
    return process_pdf(pdf_file, theme=theme)


with gr.Blocks(title="Aura Assist") as demo:
    gr.Markdown("# Aura Assist — accessible reader (Module A)")
    gr.Markdown(
        "Upload a PDF and pick a theme. Math-to-speech and the migraine "
        "knowledge agent are on the way."
    )
    with gr.Row():
        pdf_input = gr.File(label="PDF", file_types=[".pdf"])
        theme_input = gr.Dropdown(
            choices=list(THEMES.keys()), value="sepia", label="Theme"
        )
    output_html = gr.HTML(label="Accessible output")
    run_btn = gr.Button("Render")
    run_btn.click(
        fn=gradio_accessible_reader,
        inputs=[pdf_input, theme_input],
        outputs=output_html,
    )

if __name__ == "__main__":
    demo.launch()