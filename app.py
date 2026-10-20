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
import gradio as gr
from pipeline import extract, validate, prepare
from pipeline.extract import init_inprocess_vlm

# Preload in-process VLM at module level for ZeroGPU CUDA context registration
if os.environ.get("SPACE_ID") or os.environ.get("SPACES_ZERO_GPU"):
    init_inprocess_vlm()


@spaces.GPU(duration=120)
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

    with gr.Tabs():
        with gr.TabItem("🚀 Marksheet Extraction & Audit"):
            with gr.Row():
                with gr.Column(scale=1):
                    file_in = gr.File(
                        label="Upload Marksheet (CBSE / ICSE / UPMSP / BSEH / UBSE)",
                        file_types=["image", ".pdf"],
                    )
                    btn = gr.Button("⚡ Run Spatial VLM Extraction", variant="primary", size="lg")
                    gr.Examples(
                        examples=[
                            ["dataset/cbse_border_1.png"],
                            ["dataset/icse_green.png"],
                            ["dataset/up_board_10th.png"],
                            ["dataset/haryana_10th.png"],
                        ],
                        inputs=file_in,
                        label="Quick Test Samples",
                    )
                with gr.Column(scale=1):
                    json_out = gr.JSON(label="Extracted Structured Data (GBNF Constrained & Verified)")

        with gr.TabItem("📊 Architecture & Benchmark Metrics"):
            gr.Markdown(
                """
### ⚡ Day 2 Production Benchmarks vs Baseline
| Metric | UI-TARS-7B-DPO (Baseline) | Gemma-4-E2B (Day 2 Optimized) | Impact |
| :--- | :---: | :---: | :--- |
| **Average Latency** | 36.55s | **6.28s** | **4.32x Speedup** 🚀 |
| **JSON Schema Adherence** | 75.0% | **100.0%** | Guaranteed via C++ GBNF |
| **Candidate Name Accuracy**| 90.0% | **100.0%** | Spatial layout disambiguation |
| **Numeric Marks Precision**| 98.0% | **100.0%** | Self-healing arithmetic parity |
| **VRAM Footprint** | 5.7 GB | **3.2 GB** | Fits in consumer GPUs |

---
### 🌐 Full Production React Dashboard
The standalone React single-page dashboard with side-by-side visual inspection, editable tables, and export features is available in the [`frontend/`](https://github.com/Adityakeerti/DOC-OC-LLM/tree/main/frontend) directory.
Run locally via:
```bash
# Terminal 1: FastAPI Server
python3 -m uvicorn api.app:app --host 0.0.0.0 --port 8000

# Terminal 2: React Vite App
cd frontend && npm run dev
```
"""
            )

    btn.click(fn=process_marksheet_ui, inputs=file_in, outputs=json_out, api_name="process")

if __name__ == "__main__":
    demo.queue().launch()





