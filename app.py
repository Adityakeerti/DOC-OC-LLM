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

import gradio as gr

try:
    import gradio_client.utils
    _orig_get_type = gradio_client.utils.get_type
    def _safe_get_type(schema):
        if isinstance(schema, bool):
            return "boolean"
        return _orig_get_type(schema)
    gradio_client.utils.get_type = _safe_get_type
except Exception as e:
    print(f"gradio_client patch notice: {e}")

from pipeline import extract, validate, prepare



@spaces.GPU(duration=60)
def process_marksheet_ui(file_input):
    if file_input is None:
        return {"error": "Please select or upload a marksheet file."}
    try:
        # file_input is either a file path or file-like object provided by Gradio
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


with gr.Blocks(title="DOC-OC v2 Universal Marksheet Engine", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 📑 DOC-OC v2 — Universal Marksheet Extraction Engine")
    gr.Markdown(
        "**High-Performance Vision-Language Model Extraction Engine for Multi-Board Indian Academic Documents**  \n"
        "*Offline VLM Edge Architecture • Deterministic GBNF Schema • Self-Healing Arithmetic • Apache-2.0 License*"
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

if __name__ == "__main__":
    demo.queue().launch()




