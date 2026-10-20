"""
app.py — FastAPI server for DOC-OC v6.

Single endpoint: upload a marksheet image → get structured JSON back.
Ties together the three pipeline modules: preprocess → extract → validate.

Run with:  python app.py
"""

import os
import io
import base64
import time
import tempfile
import json
import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from pipeline import prepare, extract, validate

LOG_FILE = Path(__file__).resolve().parent.parent / "log.txt"

def get_next_run_number() -> int:
    if not LOG_FILE.exists():
        return 1
    try:
        content = LOG_FILE.read_text(encoding="utf-8")
        matches = re.findall(r"RUN-(\d+)", content)
        if matches:
            return max(int(m) for m in matches) + 1
    except Exception:
        pass
    return 1

def log_run(run_no: int, filename: str, result_dict: dict = None, warnings: list = None, timing: dict = None, error: str = None):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = "================================================================================\n"
    entry += f"RUN-{run_no} - {now_str}\n"
    entry += f"File: {filename}\n"
    if error:
        entry += f"ERROR: {error}\n"
    else:
        t_pre = timing.get('preprocess', 0) if timing else 0
        t_ext = timing.get('extract', 0) if timing else 0
        t_val = timing.get('validate', 0) if timing else 0
        total = round(t_pre + t_ext + t_val, 2)
        entry += f"Timing: Preprocess: {t_pre}s | Extract: {t_ext}s | Validate: {t_val}s | Total: {total}s\n"
        if warnings:
            entry += f"Warnings: {json.dumps(warnings)}\n"
        entry += "JSON:\n"
        payload_str = json.dumps(result_dict, indent=2, ensure_ascii=False)
        entry += f"{payload_str}\n"
    entry += "================================================================================\n\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as e:
        print(f"Failed to write to {LOG_FILE}: {e}")

# ── App Setup ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="DOC-OC v6",
    description="Universal Marksheet Extractor — powered by local VLMs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount dataset folder for sample previews
dataset_dir = Path(__file__).resolve().parent.parent / "dataset"
if dataset_dir.exists():
    app.mount("/dataset", StaticFiles(directory=str(dataset_dir)), name="dataset")

frontend_assets = Path(__file__).resolve().parent.parent / "frontend" / "dist" / "assets"
if frontend_assets.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_assets)), name="frontend_assets")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.post("/process")
async def process_marksheet(file: UploadFile = File(...)):
    """
    Upload a marksheet (JPG, PNG, or PDF) and get extracted data.

    Returns JSON with: data, warnings, timing
    """
    contents = await file.read()
    suffix = Path(file.filename).suffix or ".jpg"

    # Save upload to a temp file (preprocess needs a file path)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(contents)
    tmp.close()

    run_no = get_next_run_number()

    try:
        # Step 1: Preprocess — load, fix orientation, resize
        t0 = time.time()
        image = prepare(tmp.name)
        t_preprocess = time.time() - t0

        # Step 2: Extract — send image to VLM, get JSON
        t0 = time.time()
        raw_data = extract(image)
        t_extract = time.time() - t0

        # Step 3: Validate — type-check and sanity-check the result
        t0 = time.time()
        marksheet, warnings = validate(raw_data)
        t_validate = time.time() - t0

        result_data = marksheet.model_dump()
        timing_data = {
            "preprocess": round(t_preprocess, 2),
            "extract": round(t_extract, 2),
            "validate": round(t_validate, 2),
        }

        # Generate high-resolution web-ready preview data URL (works for PDFs and photos alike)
        preview_buffer = io.BytesIO()
        image.save(preview_buffer, format="JPEG", quality=85)
        encoded_preview = base64.b64encode(preview_buffer.getvalue()).decode("utf-8")
        preview_data_url = f"data:image/jpeg;base64,{encoded_preview}"

        # Save to log.txt
        log_run(run_no, file.filename, result_dict=result_data, warnings=warnings, timing=timing_data)

        return JSONResponse(content={
            "data": result_data,
            "warnings": warnings,
            "timing": timing_data,
            "image_preview": preview_data_url,
        })

    except RuntimeError as e:
        log_run(run_no, file.filename, error=str(e))
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        log_run(run_no, file.filename, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.unlink(tmp.name)


@app.post("/submit")
async def submit_marksheets(payload: dict):
    """Save submitted student marksheet batch."""
    run_no = get_next_run_number()
    marksheets = payload.get("marksheets", [])
    log_run(run_no, f"BATCH-SUBMIT ({len(marksheets)} documents)", result_dict=payload)
    return {"status": "success", "count": len(marksheets), "run": run_no}


@app.get("/samples")
async def list_samples():
    """List preloaded multi-board sample documents."""
    return [
        {"name": "CBSE 10th Standard", "board": "CBSE", "file": "cbse_border_1.png", "url": "/dataset/cbse_border_1.png"},
        {"name": "CBSE 12th Senior Secondary", "board": "CBSE", "file": "12_3.jpg", "url": "/dataset/12_3.jpg"},
        {"name": "ICSE 10th Certificate", "board": "ICSE", "file": "icse_green.png", "url": "/dataset/icse_green.png"},
        {"name": "ISC 12th Certificate", "board": "CISCE", "file": "10_1.jpg", "url": "/dataset/10_1.jpg"},
        {"name": "UP Board 10th (UPMSP Pink)", "board": "UPMSP", "file": "up_board_10th.png", "url": "/dataset/up_board_10th.png"},
        {"name": "BSEH Haryana 10th (Green)", "board": "BSEH", "file": "haryana_10th.png", "url": "/dataset/haryana_10th.png"},
        {"name": "BSEH Haryana 12th", "board": "BSEH", "file": "haryana_12th.png", "url": "/dataset/haryana_12th.png"},
        {"name": "UBSE Uttarakhand 10th", "board": "UBSE", "file": "state_sample_ms7.jpg", "url": "/dataset/state_sample_ms7.jpg"},
    ]


@app.get("/ui")
@app.get("/app")
async def serve_ui():
    """Serve the compiled React frontend if built, otherwise split-screen test UI."""
    dist_index = Path(__file__).resolve().parent.parent / "frontend" / "dist" / "index.html"
    if dist_index.exists():
        return FileResponse(dist_index)
    ui_path = Path(__file__).resolve().parent.parent / "UI.html"
    if ui_path.exists():
        return FileResponse(ui_path)
    return JSONResponse({"message": "DOC-OC v6 API running"})



@app.get("/health")
async def health():
    """Quick check that the API is running."""
    return {"status": "ok"}


# ── Run directly ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    print("Starting DOC-OC v6 API on http://localhost:8000")
    print("Docs available at http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
