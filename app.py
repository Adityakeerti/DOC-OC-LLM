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
from fastapi.responses import RedirectResponse
from pipeline import extract, validate, prepare
from api.app import app


@spaces.GPU(duration=60)
def process_marksheet_ui(file_input):
    if file_input is None:
        return {"error": "Please select or upload a marksheet file."}
    try:
        prepared_img = prepare(file_input)
        raw = extract(prepared_img)
        validated, warnings = validate(raw)
        return {
            "status": "success",
            "data": validated.model_dump(),
            "warnings": warnings,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


with gr.Blocks(title="DOC-OC v2 Universal Marksheet Engine") as demo:
    gr.Markdown("# 📑 DOC-OC v2 — Universal Marksheet Extraction Engine")
    gr.Markdown(
        "⚡ **Production React Dashboard**: Active at root [**/**](/).\n\n"
        "📖 **Interactive Swagger Docs**: Available at [**/docs**](/docs).\n\n"
        "🧪 **ZeroGPU Live Extractor**:"
    )

    with gr.Row():
        with gr.Column(scale=1):
            file_in = gr.File(
                label="Upload Marksheet (CBSE / ICSE / State Board)",
                file_types=["image", ".pdf"],
            )
            btn = gr.Button("🚀 Extract Structured Marksheet Data", variant="primary", size="lg")
        with gr.Column(scale=1):
            json_out = gr.JSON(label="Extracted Structured Data (GBNF Constrained & Verified)")

    btn.click(fn=process_marksheet_ui, inputs=file_in, outputs=json_out, api_name="process")

demo.queue()

# Mount Gradio onto the FastAPI app at /gradio
app = gr.mount_gradio_app(app, demo, path="/gradio")

@app.get("/config")
async def forward_config():
    return RedirectResponse(url="/gradio/config")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    print(f"🚀 Starting DOC-OC v2 on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)





