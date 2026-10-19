"""
DOC-OC v2 — Server Entry Point (FastAPI + Hugging Face Gradio Runner)
"""

import os
import uvicorn
from api.app import app

# Mount Gradio Blocks so Hugging Face Spaces detects Gradio SDK seamlessly
try:
    import gradio as gr

    with gr.Blocks(title="DOC-OC v2 Backend") as demo:
        gr.Markdown("# DOC-OC v2 — Universal Marksheet Extraction Engine")
        gr.Markdown(
            "The production React workspace is actively running at root [**/**](/). "
            "FastAPI REST endpoints and Swagger documentation are at [**/docs**](/docs)."
        )

    app = gr.mount_gradio_app(app, demo, path="/gradio")
except Exception as e:
    print(f"Gradio mounting notice: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    print(f"🚀 Starting DOC-OC v2 on http://0.0.0.0:{port}")
    print(f"📖 Interactive Swagger Docs: http://localhost:{port}/docs")
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
