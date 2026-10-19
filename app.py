"""
DOC-OC v2 — Server Entry Point (FastAPI + Hugging Face Gradio Runner)
"""

import os
import uvicorn
from api.app import app

# ZeroGPU decorator support
try:
    import spaces
except ImportError:
    class spaces:
        @staticmethod
        def GPU(fn=None, duration=60):
            if fn is None:
                return lambda f: f
            return fn

# Mount Gradio Blocks with an explicit @spaces.GPU function for ZeroGPU validation
try:
    import gradio as gr
    from pipeline import extract, validate, prepare

    @spaces.GPU(duration=60)
    def gradio_extract(image_input):
        if image_input is None:
            return {"error": "No marksheet image provided"}
        try:
            prepared_img = prepare(image_input)
            raw = extract(prepared_img)
            validated, warnings = validate(raw)
            return {
                "data": validated.model_dump(),
                "warnings": warnings,
            }
        except Exception as e:
            return {"error": str(e)}

    with gr.Blocks(title="DOC-OC v2 Universal Marksheet Engine") as demo:
        gr.Markdown("# DOC-OC v2 — Universal Marksheet Extraction Engine")
        gr.Markdown(
            "⚡ **Production Web App**: Running actively at root [**/**](/) with high-fidelity side-by-side verification.\n\n"
            "📖 **Interactive Swagger Docs**: Available at [**/docs**](/docs).\n\n"
            "🧪 **Interactive ZeroGPU Runner**:"
        )
        with gr.Row():
            with gr.Column():
                img_in = gr.Image(type="pil", label="Upload Marksheet (CBSE / ICSE / State Board)")
                btn = gr.Button("Extract Marksheet Data", variant="primary")
            with gr.Column():
                json_out = gr.JSON(label="Structured Marksheet JSON")

        btn.click(fn=gradio_extract, inputs=img_in, outputs=json_out)

    app = gr.mount_gradio_app(app, demo, path="/gradio")
except Exception as e:
    print(f"Gradio mounting notice: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    print(f"🚀 Starting DOC-OC v2 on http://0.0.0.0:{port}")
    print(f"📖 Interactive Swagger Docs: http://localhost:{port}/docs")
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)

