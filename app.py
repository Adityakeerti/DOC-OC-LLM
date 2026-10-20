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
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import gradio as gr

from pipeline import extract, validate, prepare
from api.app import app as fastapi_app


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


with gr.Blocks(title="DOC-OC v2 Universal Marksheet Engine", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 📑 DOC-OC v2 — Universal Marksheet Extraction Engine")
    gr.Markdown(
        "⚡ **Production React Dashboard**: Open full workspace at [**/ui**](/ui) or [**/app**](/app).\n\n"
        "📖 **Interactive Swagger Docs**: Available at [**/api/docs**](/api/docs).\n\n"
        "🧪 **ZeroGPU Live Extractor** (Powered by Gemma-4-E2B):"
    )
    with gr.Row():
        with gr.Column():
            img_in = gr.Image(type="pil", label="Upload Marksheet (CBSE / ICSE / State Board)")
            btn = gr.Button("Extract Marksheet Data", variant="primary")
        with gr.Column():
            json_out = gr.JSON(label="Structured Marksheet JSON")

    btn.click(fn=gradio_extract, inputs=img_in, outputs=json_out, api_name="process")

# Pre-initialize Gradio's internal FastAPI app and attach our routes
gr_app = gr.routes.App.create_app(demo)

# Mount our custom FastAPI app endpoints onto Gradio's app
gr_app.mount("/api", fastapi_app)

# Mount dataset sample images for UI
dataset_dir = Path(__file__).resolve().parent / "dataset"
if dataset_dir.exists():
    gr_app.mount("/dataset", StaticFiles(directory=str(dataset_dir)), name="dataset")

# Mount React assets
frontend_assets = Path(__file__).resolve().parent / "frontend" / "dist" / "assets"
if frontend_assets.exists():
    gr_app.mount("/assets", StaticFiles(directory=str(frontend_assets)), name="frontend_assets")

# Expose /ui, /app, and /health directly on Gradio's server
@gr_app.get("/health")
async def health():
    return {"status": "ok"}

@gr_app.get("/ui")
@gr_app.get("/app")
async def serve_react_ui():
    dist_index = Path(__file__).resolve().parent / "frontend" / "dist" / "index.html"
    if dist_index.exists():
        return FileResponse(dist_index)
    return JSONResponse({"message": "DOC-OC v2 UI running on /"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    print(f"🚀 Starting DOC-OC v2 via Gradio ZeroGPU on port {port}")
    demo.queue().launch(
        server_name="0.0.0.0",
        server_port=port,
        show_error=True,
    )



