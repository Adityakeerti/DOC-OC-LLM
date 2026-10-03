# DOC-OC v6 — Master Architecture, State & Execution Plan for Next Agent

> **Project Goal**: Universal Indian Marksheet & Certificate Extractor using local Vision-Language Models (VLMs). Zero cloud OCR APIs, zero hardcoded regex, zero cost-per-page. Production-ready, portfolio-grade code with 100% line-by-line understanding.

---

## 1. System Environment & Hardware Specs

* **Operating System**: Linux (x86_64, Arch Linux)
* **GPU**: NVIDIA GeForce RTX 4050 Laptop (6141 MiB VRAM)
* **Python Virtual Environment**: `/home/aditya/Desktop/STUDY/DOC OC v6/.venv`
  * Activated via: `source .venv/bin/activate` or direct binary `.venv/bin/python`
* **Inference Engine**: Local `llama-server` compiled at:
  `/home/aditya/llama-fork/build/bin/llama-server`
* **Model Storage Directory**: `/home/aditya/AI/models/`
  * `Gemma-4-E2B`: `/home/aditya/AI/models/Gemma-4-E2B/gemma-4-E2B_q4_0-it.gguf` + `gemma-4-E2B-it-mmproj.gguf`
  * `UI-TARS-7B-DPO`: `/home/aditya/AI/models/UI-TARS-7B-DPO/UI-TARS-7B-DPO-Q4_K_M.gguf` + `mmproj-UI-TARS-7B-DPO-f16.gguf`
  * `Qwen2.5-VL` (3B & 7B): Downloading by user in separate terminal.

---

## 2. Clean Project Directory Structure

The repository has been organized into clear, functional categories:

```
DOC OC v6/
│
├── api/                           ← Backend API package
│   ├── __init__.py
│   └── app.py                     ← FastAPI server (/process, /health)
│
├── pipeline/                      ← Core VLM extraction logic
│   ├── __init__.py                ← Re-exports: prepare, extract, validate
│   ├── preprocess.py              ← EXIF rotation, proportional resize to 1600px
│   ├── extract.py                 ← VLM HTTP client (httpx), system prompt, JSON cleanup
│   └── validate.py                ← Pydantic schemas (Marksheet, Subject, StudentInfo) + arithmetic checks
│
├── dataset/                       ← 37 authentic multi-board marksheets
│   ├── manifest.json              ← Metadata catalog (splits, boards, dimensions)
│   ├── README.md                  ← Dataset documentation
│   ├── build_manifest.py          ← Script to re-index dataset & regenerate manifest
│   ├── ground_truth/              ← Hand-audited gold JSON labels (10 completed)
│   └── [37 image files]           ← CBSE, ICSE, Uttarakhand, Haryana, UP board scans
│
├── benchmarks/                    ← Benchmark & evaluation scripts
│   ├── benchmark.py               ← Batch runner
│   ├── run_test_and_save.py       ← Gemma test suite
│   └── run_uitars_benchmark.py    ← UI-TARS test suite
│
├── results/                       ← Empirical evaluation logs
│   ├── result_gemma.txt           ← Full Gemma benchmark log (8/8 success, 26s avg)
│   └── result_UITARS.txt          ← Full UI-TARS benchmark log (6/8 success, 36s avg)
│
├── training/                      ← Fine-tuning & few-shot experimentation
│   └── test_few_shot.py           ← In-context few-shot prompt testing
│
├── scripts/                       ← Operational helper scripts
│   └── start_server.sh            ← Starts llama-server with UI-TARS or Gemma
│
├── app.py                         ← Root entry point (runs uvicorn api.app:app)
├── start_server.sh                ← Root symlink/launcher for easy access
├── requirements.txt               ← Minimal dependencies (no heavy Torch in core app!)
├── plan.md                        ← Architectural master plan
└── prompt.md                      ← THIS FILE (Context & instructions for next agent)
```

---

## 3. Benchmark Summary & Empirical Findings

Both `Gemma-4-E2B` and `UI-TARS-7B-DPO` were benchmarked on 8 authentic marksheets (`10_1` to `12_4`):

| Evaluation Metric | **Gemma-4-E2B** (`results/result_gemma.txt`) | **UI-TARS-7B-DPO** (`results/result_UITARS.txt`) | Takeaway |
| :--- | :---: | :---: | :--- |
| **Numeric Marks Accuracy** | **98%** | **98%** | Both read tables & numbers with near-zero error. |
| **Roll Number Precision** | **100%** | **100%** | Exact digit matches across all boards. |
| **Candidate Name Accuracy** | 70% | **90%** | UI-TARS resolves candidate vs. parent names far better. |
| **Table Hierarchy Grouping** | Flattens rows (13 sub-papers) | Smart grouping (7 composite subjects) | UI-TARS understands parent/sub-component indentation. |
| **JSON Schema Adherence** | **100%** (8/8 parsed) | 75% (6/8 parsed) | UI-TARS occasionally outputs leading zeros (`077`). |
| **Average Latency** | **26.46s** | **36.55s** | Gemma is ~38% faster. |

---

## 4. Immediate Roadmap for Next Agent

### Task 1: Complete Few-Shot Prompt Evaluation
1. **File**: `training/test_few_shot.py`
2. **Context**: Gemma failed on `dataset/12_3.jpg` by picking the Mother's name (`MANJU JAISAL`) instead of the Candidate's name (`VANSH JAISWAL`).
3. **Goal**: Run `training/test_few_shot.py` with `llama-server` running Gemma to prove that few-shot in-context rules resolve the name ambiguity without retraining.
4. **Command**:
   ```bash
   ./scripts/start_server.sh gemma   # in background or separate terminal
   .venv/bin/python training/test_few_shot.py
   ```

### Task 2: Architecture Shrinking & Fine-Tuning Setup
1. **Target Architecture**: Qwen2.5-VL-3B or Gemma-4-E2B.
2. **Why 3B**: 3B parameters fit entirely within 3GB VRAM, allowing 100% GPU offload, <12s inference, and room for 16k context window.
3. **Dataset Preparation**:
   * Use `dataset/manifest.json` and `dataset/ground_truth/` (10 verified ground truth JSONs already exist).
   * Annotate remaining images in `dataset/` using `pipeline/extract.py` with human-in-the-loop review.
   * Format dataset into standard VLM conversational JSONL (e.g. LLaVA / ShareGPT format):
     ```json
     {
       "id": "10_1",
       "image": "dataset/10_1.jpg",
       "conversations": [
         {"from": "human", "value": "<image>\nExtract marksheet data to JSON."},
         {"from": "gpt", "value": "{...ground_truth_json...}"}
       ]
     }
     ```
4. **LoRA Fine-Tuning Configuration**:
   * Tooling: Unsloth, Hugging Face `peft` + `trl` (SFTTrainer), or `llama.cpp` LoRA finetune.
   * Target layers: Attention projections (`q_proj`, `k_proj`, `v_proj`, `o_proj`) + multimodal projector.
   * Rank: $r=16$, $\alpha=32$.
   * Quantization: 4-bit QLoRA to train directly on the laptop's RTX 4050 without OOM.

### Task 3: ZeroGPU / Cloud Deployment (Option 2)
1. User decided on **Option 2 (Hugging Face Spaces with ZeroGPU)**.
2. Structure a Hugging Face Space repository:
   * Create `app.py` using Gradio or FastAPI with `@spaces.GPU`.
   * Load the fine-tuned or base VLM (`Qwen2.5-VL-7B-Instruct` or `Qwen2.5-VL-3B-Instruct`).
   * Add interactive PDF/Image upload and JSON view.
3. Alternative: Expose the local FastAPI server using Cloudflare Tunnel:
   ```bash
   cloudflared tunnel --url http://localhost:8000
   ```

---

## 5. Quick Verification Commands for the Next Agent

```bash
# 1. Activate venv
source .venv/bin/activate

# 2. Check server status / port
curl -s http://localhost:8080/health

# 3. Start VLM server
./scripts/start_server.sh          # for UI-TARS-7B-DPO
./scripts/start_server.sh gemma    # for Gemma-4-E2B

# 4. Start FastAPI server
python app.py                      # runs on http://localhost:8000 (docs at /docs)

# 5. Run full benchmark test suite
python benchmarks/benchmark.py
```
