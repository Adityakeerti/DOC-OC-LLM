"""
app.py — FastAPI server for DOC-OC v6.

Single endpoint: upload a marksheet image → get structured JSON back.
Ties together the three pipeline modules: preprocess → extract → validate.

Run with:  python app.py
"""

import os
import time
import tempfile
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

from pipeline import prepare, extract, validate


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

        return JSONResponse(content={
            "data": marksheet.model_dump(),
            "warnings": warnings,
            "timing": {
                "preprocess": round(t_preprocess, 2),
                "extract": round(t_extract, 2),
                "validate": round(t_validate, 2),
            },
        })

    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.unlink(tmp.name)


@app.get("/")
async def serve_ui():
    """Serve the split-screen test UI."""
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
