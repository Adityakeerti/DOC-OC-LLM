# DOC-OC v6 — Universal Indian Marksheet & Certificate Extractor

**High-Performance Vision-Language Model Extraction Engine for Multi-Board Indian Academic Documents**  
*Zero Cloud OCR APIs • Zero Regex • Zero Cost-Per-Page • 100% Offline GPU Inference*

---

## ⚡ Key Performance Metrics (Day 2 Benchmarks)

| Metric | UI-TARS-7B-DPO (Baseline) | Gemma-4-E2B (Day 1 Zero-Shot) | **Gemma-4-E2B (Day 2 Optimized)** | Impact |
| :--- | :---: | :---: | :---: | :--- |
| **Average Latency** | 36.55s | 27.12s | **6.28s** | **4.32x Speedup** 🚀 |
| **JSON Schema Adherence** | 75.0% (failed on leading zeros) | 100.0% | **100.0%** (C++ GBNF Locked) | Mathematically guaranteed |
| **Candidate Name Accuracy**| 90.0% | 70.0% (picked mother's name) | **100.0%** | Resolved via layout grounding |
| **Numeric Marks Precision**| 98.0% | 98.0% | **100.0%** | Self-healing arithmetic |
| **VRAM Footprint** | 5.7 GB (Saturated) | 2.7 GB | **3.2 GB** (100% GPU Offload) | Fits comfortably in 6GB VRAM |
| **Cost Per Page** | $0.00 | $0.00 | **$0.00** | Pure edge inference |

---

## 🏗️ Architectural Innovation: The 3-Pillar Engine

Legacy marksheet extraction systems (v1–v5) used brittle multi-stage cascades: Canny contour cropping, YOLO logo detectors, Haar cascades, TableTransformers, paid third-party OCR APIs ($0.02–$0.05/page), and hardcoded regex parsers that shattered whenever a state board changed layout or background color (UP pink, Haryana green).

**DOC-OC v6 eliminates the entire cascade in favor of a unified spatial VLM pipeline**:

```
                       DOC-OC v6 EXTRACTION PIPELINE
  ┌────────────────────────────────────────────────────────────────────────┐
  │ 1. NON-DESTRUCTIVE PREPROCESSING (pipeline/preprocess.py)              │
  │    • PyMuPDF 2× matrix rasterization for vector-crisp text             │
  │    • Auto-EXIF orientation correction for mobile camera uploads        │
  │    • Proportional 1200px Lanczos scaling (43% fewer visual tokens)     │
  ├────────────────────────────────────────────────────────────────────────┤
  │ 2. C++ GBNF CONSTRAINED INFERENCE (pipeline/extract.py)                │
  │    • llama.cpp local server running Gemma-4-E2B (100% GPU offload)     │
  │    • Token-level logit masking via GBNF JSON Schema                    │
  │    • Reasoning traces disabled (eliminates 1500+ token thinking lag)   │
  │    • In-context layout grounding (Candidate Name vs. Parent Name)      │
  ├────────────────────────────────────────────────────────────────────────┤
  │ 3. SELF-HEALING ARITHMETIC VALIDATION (pipeline/validate.py)           │
  │    • Pydantic model validation with strict type enforcement            │
  │    • Arithmetic cross-check (Theory + Practical == Total Obtained)     │
  │    • Automated reconciliation of max marks vs. obtained marks          │
  └────────────────────────────────────────────────────────────────────────┘
```

---

## 🔬 Deep ML Systems Engineering & Optimization

### 1. Eliminating Reasoning Lag (4.3x Speedup)
Modern reasoning VLMs (like Gemma 4) default to generating internal thought chains (`reasoning_content`) before emitting the final answer. In a structured extraction task, this generated >1,500 conversational thinking tokens per request, bloating latency to 27+ seconds.  
By configuring `llama-server` with `--reasoning off` and `--reasoning-budget 0`, generation is redirected purely to the output JSON, dropping extraction time to **4.2s–6.8s per document** at 83 tokens/second on an RTX 4050 Laptop GPU.

### 2. C++ GBNF Grammar Constrained Decoding
Standard autoregressive sampling often produces formatting defects like markdown wrappers (````json```), trailing commas, or leading zero octal violations (e.g. `077`).  
We compile the Pydantic schema into a strict GBNF grammar passed directly to the inference engine. The C++ sampler masks all illegal token logits, making syntax errors physically impossible.

### 3. ShortGPT Layer Redundancy Profiling
Using the ShortGPT block importance algorithm, we measured layer-to-layer cosine similarity and angular distance across all 35 transformer blocks:
- **Early Blocks (0–5)**: Cosine similarity 0.75–0.79 (critical for visual spatial token grounding).
- **Middle Blocks (12–20)**: Peak redundancy at **Blocks 14 & 15 (Cosine Sim 0.8953, Angular Dist 0.1470)**.
- **Architectural Discovery**: While standard 7B models (like UI-TARS) have independent layers, Gemma-4-E2B incorporates **Per-Layer Embeddings (PLE)** (`[8960, 262144]`) and shared KV attention layers. Because Phase 1 optimizations already brought latency down to 6.28s, surgical weight pruning was determined to be an unnecessary stability risk.

---

## 📂 Repository Structure

```
DOC-OC-v6/
│
├── api/                           ← Backend API package
│   ├── __init__.py
│   └── app.py                     ← FastAPI server (/process, /health, UI mount)
│
├── pipeline/                      ← Core VLM extraction logic
│   ├── __init__.py                ← Re-exports: prepare, extract, validate
│   ├── preprocess.py              ← EXIF rotation, Lanczos 1200px resize
│   ├── extract.py                 ← VLM HTTP client with GBNF schema constraints
│   └── validate.py                ← Pydantic schemas + self-healing arithmetic
│
├── dataset/                       ← 37 authentic multi-board marksheets
│   ├── manifest.json              ← Metadata catalog (splits, boards, dimensions)
│   ├── ground_truth/              ← Hand-audited gold JSON labels (10 completed)
│   └── [37 image files]           ← CBSE, ICSE, UP, Haryana, Uttarakhand boards
│
├── benchmarks/                    ← Benchmark & evaluation scripts
│   ├── benchmark.py               ← Batch runner
│   ├── run_test_and_save.py       ← Automated benchmark runner
│   └── run_uitars_benchmark.py    ← UI-TARS test suite
│
├── results/                       ← Empirical evaluation logs
│   ├── result_phase1_gemma.txt    ← Day 2 Optimized Gemma log (6.28s avg, 100% pass)
│   ├── result_gemma.txt           ← Day 1 Baseline Gemma log (27.12s avg)
│   └── result_UITARS.txt          ← Day 1 UI-TARS log (36.55s avg)
│
├── training/                      ← Fine-tuning & layer profiling
│   ├── prepare_dataset.py         ← Compiles 37 samples into conversational JSONL
│   ├── analyze_layers.py          ← ShortGPT layer redundancy & cosine similarity
│   └── data/                      ← train.jsonl (25), val.jsonl (6), test.jsonl (6)
│
├── docs/                          ← Technical documentation & interview logs
│   ├── README.md                  ← Master documentation index & reading guide
│   ├── process.md                 ← Chronological engineering decision log (12+ steps)
│   ├── plan.md                    ← Architectural blueprint & roadmap
│   ├── tasks.md                   ← Master engineering checklist
│   ├── prompt.md                  ← VLM prompt engineering & schema constraints
│   └── day2-night-auto.md         ← Overnight autonomous execution playbook
│
├── UI.html                        ← Split-screen interactive testing UI
├── start_server.sh                ← Launch script (100% GPU offload, Gemma/Qwen/UI-TARS)
├── app.py                         ← Root server entry point (python app.py)
└── requirements.txt               ← Lightweight dependencies (no heavy Torch in core app)
```

---

## 📖 Engineering Documentation

Comprehensive deep-dives, architectural trade-offs, and benchmarks are indexed in [`docs/`](docs/README.md):
- **[`docs/process.md`](docs/process.md)**: Detailed chronological log of every technical challenge and solution for system design interview prep.
- **[`docs/plan.md`](docs/plan.md)**: Master plan detailing hardware sizing, VRAM budgets, and optimization milestones.
- **[`docs/tasks.md`](docs/tasks.md)**: Granular task status checklist.
- **[`docs/prompt.md`](docs/prompt.md)**: Prompt evolution, layout grounding, and schema designs.
- **[`docs/day2-night-auto.md`](docs/day2-night-auto.md)**: Overnight autonomous workflow and benchmark orchestration.

---

## 🚀 Quickstart

### 1. Requirements
- **OS**: Linux (x86_64, tested on Arch Linux)
- **GPU**: NVIDIA GPU with ≥6 GB VRAM (RTX 4050 Laptop or higher)
- **Local Engine**: `llama.cpp` (`llama-server`) with CUDA support

### 2. Environment Setup
```bash
git clone https://github.com/Adityakeerti/DOC-OC-LLM.git
cd DOC-OC-LLM
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Launch Inference Server
```bash
./start_server.sh gemma   # 100% GPU offloaded, reasoning off, 6.28s latency
```

### 4. Run API Server & Benchmark
```bash
# Start FastAPI backend
python app.py             # Swagger docs available at http://localhost:8000/docs

# Run full empirical benchmark
python benchmarks/run_test_and_save.py results/result_phase1_gemma.txt
```

---

## 📜 License
Apache-2.0 License. Designed and engineered for production-grade, local document intelligence.
