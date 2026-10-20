# ZeroGPU decorator support — MUST BE THE VERY FIRST IMPORT
try:
    import spaces
except ImportError:
    class spaces:
        @staticmethod
        def GPU(fn=None, duration=60):
            if fn is None:
                return lambda f: f
            return fn

import os
import uvicorn
import gradio as gr
from pipeline import extract, validate, prepare
from api.app import app


@spaces.GPU
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


with gr.Blocks(title="DOC-OC v2 Universal Marksheet Engine", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 📑 DOC-OC v2 — Universal Marksheet Extraction Engine")
    gr.Markdown(
        "⚡ **Production React Dashboard**: Open full workspace at [**/ui**](/ui) or [**/app**](/app).\n\n"
        "📖 **Interactive Swagger Docs**: Available at [**/docs**](/docs).\n\n"
        "🧪 **ZeroGPU Live Extractor** (Powered by Gemma-4-E2B):"
    )
    with gr.Row():
        with gr.Column():
            img_in = gr.Image(type="pil", label="Upload Marksheet (CBSE / ICSE / State Board)")
            btn = gr.Button("Extract Marksheet Data", variant="primary")
        with gr.Column():
            json_out = gr.JSON(label="Structured Marksheet JSON")

    btn.click(fn=gradio_extract, inputs=img_in, outputs=json_out)

# MANDATORY FOR ZEROGPU: Explicitly enable Gradio concurrency queue before mounting
demo.queue(default_concurrency_limit=None)

# Mount Gradio at root path "/" so ZeroGPU supervisor scans /config cleanly
app = gr.mount_gradio_app(app, demo, path="/")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    print(f"🚀 Starting DOC-OC v2 on http://0.0.0.0:{port}")
    print(f"📖 Interactive Swagger Docs: http://localhost:{port}/docs")
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)


