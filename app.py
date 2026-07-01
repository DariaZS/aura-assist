"""
Aura Assist — Flask API.

Serves the accessible reader as a small JSON API. Run this alongside
demo.py (the Gradio UI) — they're separate processes because Flask (WSGI)
and Gradio's mount hook (which needs an ASGI app like FastAPI) don't glue
together directly.

    python app.py     -> API on http://localhost:5000
    python demo.py     -> Demo UI on http://localhost:7860
"""

import os
import tempfile

from flask import Flask, jsonify, request

from src.accessible_reader import process_pdf

flask_app = Flask(__name__)


@flask_app.route("/health")
def health():
    return jsonify({"status": "ok"})


@flask_app.route("/api/accessible-reader", methods=["POST"])
def accessible_reader_api():
    """Accepts a PDF upload + optional theme, returns themed HTML."""
    if "file" not in request.files:
        return jsonify({"error": "no file uploaded"}), 400

    uploaded = request.files["file"]
    theme = request.form.get("theme", "sepia")

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        uploaded.save(tmp.name)
        html = process_pdf(tmp.name, theme=theme)
    os.unlink(tmp.name)

    return jsonify({"html": html})


if __name__ == "__main__":
    flask_app.run(debug=True, port=5000)