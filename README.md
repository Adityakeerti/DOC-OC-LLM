# DOC-OC v6

**Universal Marksheet Extractor** — Extract structured data from any Indian education board marksheet using local Vision-Language Models.

Zero cloud APIs. Zero cost per page. Works offline.

---

## How It Works

```
Marksheet Image/PDF
       │
       ▼
  preprocess.py      →  Fix orientation, resize (no cropping)
       │
       ▼
  extract.py         →  Send to local VLM, get structured JSON
       │
       ▼
  validate.py        →  Type-check, arithmetic sanity check
       │
       ▼
  Structured JSON     →  Student info, subjects, marks, result
```

One VLM call replaces the entire old pipeline (YOLO + TableTransformer + paid OCR API + regex parsers).

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the VLM server

```bash
chmod +x start_server.sh
./start_server.sh            # UI-TARS-7B-DPO (best accuracy)
# or
./start_server.sh gemma      # Gemma-4-E2B (faster)
```

### 3. Run the API

```bash
python app.py
# → http://localhost:8000/docs
```

### 4. Test with a marksheet

```bash
curl -X POST http://localhost:8000/process \
  -F "file=@dataset/10_1.jpg"
```

### 5. Benchmark all images

```bash
python benchmark.py
# Results saved to results/
```

---

## Project Structure

```
DOC-OC-v6/
│
├── pipeline/                 ← Core logic (Python package)
│   ├── __init__.py               exports: prepare, extract, validate
│   ├── preprocess.py             load image, fix EXIF, resize
│   ├── extract.py                send to VLM, get JSON
│   └── validate.py               Pydantic schema + arithmetic checks
│
├── dataset/                  ← 26 marksheet images (10th + 12th class)
│
├── app.py                    ← FastAPI server (entry point)
├── benchmark.py              ← Batch testing on all images
├── start_server.sh           ← Launches local llama-server
├── requirements.txt
├── .gitignore
├── README.md
└── plan.md
```

---

## Models Used

| Model | Size | Purpose |
|-------|------|---------|
| **UI-TARS-7B-DPO** | 5.7 GB | Primary — trained on document/form understanding |
| **Gemma-4-E2B** | 4.1 GB | Fallback — faster, less VRAM |

Both run locally via [llama.cpp](https://github.com/ggml-org/llama.cpp) server. No cloud APIs, no API keys.

---

## Output Format

```json
{
  "board": "CBSE",
  "examination": "Secondary School Examination 2022",
  "student_info": {
    "name": "STUDENT NAME",
    "roll_no": "1234567",
    "father_name": "FATHER NAME",
    "school_name": "SCHOOL NAME"
  },
  "subjects": [
    {
      "name": "MATHEMATICS",
      "theory": 65,
      "practical": 15,
      "total": 80,
      "max_marks": 100,
      "grade": "B2"
    }
  ],
  "result": {
    "total_obtained": 420,
    "maximum_marks": 500,
    "percentage": "84.0%",
    "status": "PASS"
  }
}
```

---

## Hardware Requirements

- **GPU**: Any NVIDIA GPU with ≥6 GB VRAM (tested on RTX 4050 Laptop)
- **RAM**: 8 GB minimum
- **Disk**: ~6 GB for model files

---

## Tech Stack

- **VLM Inference**: llama.cpp (C++, GPU-accelerated)
- **Backend**: FastAPI + Pydantic
- **Image Processing**: Pillow, PyMuPDF
- **HTTP Client**: httpx
