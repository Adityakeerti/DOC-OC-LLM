# DOC-OC v6 — Day 2 Overnight Autonomous Execution Plan

**Author**: Antigravity AI Engineering  
**Target Repository**: `https://github.com/Adityakeerti/DOC-OC-LLM`  
**Execution Environment**: Arch Linux x86_64 | NVIDIA GeForce RTX 4050 Laptop (6141 MiB VRAM) | CUDA 13.4  
**Date**: October 4, 2026  

---

## 🎯 Executive Objectives

1. **Sub-15s Latency with 100% Accuracy**:
   - Eliminate CPU memory swapping by achieving **100% GPU offload** for model weights and KV cache.
   - Enforce **C++ GBNF Grammar Constrained Decoding** in `llama-server` so the model physically cannot generate invalid JSON, leading zeros (`077`), or markdown wrappers.
   - Integrate **few-shot layout disambiguation** into the core pipeline to permanently resolve candidate name vs. parent name ambiguity.
2. **Qwen2.5-VL-3B vs. Gemma-4-E2B Head-to-Head Shootout**:
   - The freshly downloaded `Qwen2.5-VL-3B-Instruct-Q4_K_M` (1.8 GB LLM + 1.3 GB mmproj) fits 100% inside 3.5GB VRAM.
   - Benchmark both compact 2B–3B models across the test suite and compare latency, memory, and OCR extraction fidelity.
3. **Phase 2 Path A: QLoRA Fine-Tuning Setup**:
   - Format the 37-image marksheet dataset (`dataset/manifest.json` + `dataset/ground_truth/`) into ShareGPT / LLaVA multimodal conversation JSONL.
   - Set up targeted adapter training for attention projections (`q_proj`, `k_proj`, `v_proj`, `o_proj`) and multimodal projector (`mm_projector`).
   - Run training on the RTX 4050 with label masking on response tokens, evaluate against test split.
4. **Phase 2 Path B: Layer Pruning Experiment (Depth Shrinking)**:
   - **Safety First**: Backup model weights to `/home/aditya/AI/models/backups/` before any byte modification.
   - Compute layer-to-layer cosine similarity / angular distance on hidden states across calibration marksheets.
   - Excise redundant middle layers at the GGUF level, evaluate latency drop vs. accuracy retention.
5. **Git Synchronization**:
   - Maintain clean version control with progressive commits and push to `https://github.com/Adityakeerti/DOC-OC-LLM`.

---

## 📋 Pre-Flight Verification & Potential Blockers

Before running unattended overnight, we conducted full pre-flight checks:

| Check Item | Status | Details |
| :--- | :---: | :--- |
| **Local Disk Space** | ✅ **VERIFIED** | **108 GB Available** on NVMe root partition (`/dev/nvme0n1p2`). |
| **GPU VRAM & Driver** | ✅ **VERIFIED** | RTX 4050 6GB VRAM, Driver 615.71, CUDA 13.4, `llama-server` running smoothly. |
| **GitHub Authentication** | ✅ **VERIFIED** | `gh auth status` logged in as `Adityakeerti` with full `repo` write scopes. |
| **Model Weights on Disk** | ✅ **VERIFIED** | All models present locally in `/home/aditya/AI/models/`: <br>• `Gemma-4-E2B` (3.3GB + 986MB)<br>• `Qwen2.5-VL-3B-Instruct` (1.8GB + 1.3GB)<br>• `UI-TARS-7B-DPO` (4.4GB + 1.3GB) |
| **Hugging Face Hub** | ⚠️ **OPTIONAL** | Currently not logged in (`hf auth whoami` not logged in). **Not blocking**: All inference, training datasets, and models are 100% offline and local. If you want adapters pushed directly to Hugging Face Hub under your account, you can run `hf auth login` later. |

---

## 🛠️ Step-by-Step Overnight Execution Blueprint

```
                               OVERNIGHT EXECUTION TIMELINE
┌─────────────────────────┐     ┌─────────────────────────┐     ┌─────────────────────────┐
│ STEP 1: Git Init & Sync │ ──► │ STEP 2: Phase 1 Engine  │ ──► │ STEP 3: VLM Shootout    │
│ • Commit Day 1 baseline │     │ • 100% GPU Offload      │     │ • Gemma-4 vs Qwen-3B    │
│ • Push to remote repo   │     │ • GBNF Constrained JSON │     │ • Log Phase 1 Results   │
└─────────────────────────┘     └─────────────────────────┘     └─────────────────────────┘
                                                                             │
                                                                             ▼
┌─────────────────────────┐     ┌─────────────────────────┐     ┌─────────────────────────┐
│ STEP 6: Final Sync      │ ◄── │ STEP 5: Path B Pruning  │ ◄── │ STEP 4: Path A Fine-Tune│
│ • Master Matrix Table   │     │ • Backup Weights        │     │ • Format JSONL Dataset  │
│ • Git Push All Artifacts│     │ • Cosine Dist Pruning   │     │ • Train QLoRA Adapter   │
└─────────────────────────┘     └─────────────────────────┘     └─────────────────────────┘
```

### Step 1: Git Repository Initialization & Day 1 Baseline Commit
- Initialize Git repository on `main` branch linked to `https://github.com/Adityakeerti/DOC-OC-LLM.git`.
- Add clean `.gitignore` excluding bulky binary weights (`*.gguf`), `.venv/`, and temporary caches.
- Stage all core pipeline code, test scripts, manifests, ground truth JSONs, and documentation.
- Commit message: `feat(day1): baseline VLM pipeline, dataset manifest, and empirical benchmarks`.
- Push to GitHub.

### Step 2: Phase 1 High-Performance Engine & Constrained Decoding
- **Server Launcher (`start_server.sh`)**:
  - Update GPU offload from 33 layers to 100% offload (`GPU_LAYERS=35` for Gemma, `GPU_LAYERS=36` for Qwen) to eliminate CPU PCIe transfer stalls.
  - Add native launch parameter for Qwen: `./start_server.sh qwen`.
  - Enable flash attention and set context size appropriately.
- **GBNF Grammar & Schema Constrained Decoding (`pipeline/extract.py`)**:
  - Generate a strict GBNF grammar or utilize `response_format` with JSON Schema matching `pipeline/validate.py`.
  - Constrain the C++ sampler so every generated token conforms strictly to the schema (numbers are strictly digits, booleans are strictly booleans, keys match schema).
- **Layout Disambiguation Rules**:
  - Integrate few-shot disambiguation exemplars into `SYSTEM_PROMPT` to permanently fix candidate vs. parent name classification.
- **Dynamic Preprocessing**:
  - Set image resolution to 1200px Lanczos (saving ~30% visual tokens while maintaining 100% text clarity).

### Step 3: Head-to-Head VLM Shootout (Gemma-4-E2B vs. Qwen2.5-VL-3B)
- Run standardized test marksheet benchmark across CBSE, ICSE, and State boards for:
  1. `Gemma-4-E2B` with Phase 1 optimizations.
  2. `Qwen2.5-VL-3B-Instruct` with Phase 1 optimizations.
- Record:
  - Latency per document (seconds)
  - Memory / VRAM consumption (MiB)
  - Schema Adherence (100% target)
  - Candidate Name Accuracy
  - Numeric Marks Accuracy
- Save results to `results/result_phase1_engine.txt`.
- Commit and push Phase 1 results to GitHub.

### Step 4: Phase 2 Path A — QLoRA Fine-Tuning Setup
- Build dataset preparation script `training/prepare_dataset.py`:
  - Convert `dataset/manifest.json` and 10 verified ground truth JSONs in `dataset/ground_truth/` into conversational format (image + user prompt + gold JSON).
  - Create train (25), validation (6), and test (6) splits.
- Build training configuration `training/train_lora.py`:
  - Configure target modules (`q_proj`, `v_proj`, `k_proj`, `o_proj`, `mm_projector`).
  - Set rank $r=16$, $\alpha=32$, learning rate $2 \times 10^{-4}$, cosine scheduler.
  - Apply response label masking (cross-entropy loss only on assistant JSON tokens).
- Train adapter on RTX 4050, save checkpoint to `training/adapters/`.
- Evaluate adapter on test marksheets and log metrics to `results/result_finetune_lora.txt`.
- Commit adapter weights (compact ~35MB) and training scripts to GitHub.

### Step 5: Phase 2 Path B — Layer Pruning Experiment
- **Safety First**:
  - Create backup directory `/home/aditya/AI/models/backups/`.
  - Copy candidate GGUF model to backup before any modifications.
- **Redundancy Analysis**:
  - Build script `training/analyze_layers.py` to inspect layer-by-layer representations.
  - Calculate angular distance between transformer blocks across calibration inputs.
- **Model Excision**:
  - Build script `training/prune_layers.py` to prune 4–6 redundant middle blocks at GGUF level.
  - Rewire block indices (`blk.0` ... `blk.N`) and update `gemma4.block_count` or architecture metadata.
  - Save pruned model as `gemma-4-E2B-pruned.gguf`.
- **Benchmark Evaluation**:
  - Run benchmark on pruned model: test latency, VRAM drop, and accuracy retention.
  - Document findings in `results/result_pruning_experiment.txt`.

### Step 6: Master Portfolio Synthesis & GitHub Sync
- Aggregate all benchmark results into a Master Comparison Matrix in `README.md` and `plan.md`.
- Mark all completed tasks in `tasks.md`.
- Final Git commit: `feat(day2): full optimization suite, constrained decoding, benchmarks, and tuning`.
- Push everything to `https://github.com/Adityakeerti/DOC-OC-LLM`.

---

## 🔒 Safety & "Don't Break Anything" Safeguards

1. **Model Weight Backups**: No original model file is ever overwritten. All pruning outputs are written to separate files (`*-pruned.gguf`).
2. **Safe Fallback Cascade**: If any experimental model (pruned or fine-tuned) shows accuracy degradation on the test suite, the production pipeline remains locked to the verified Phase 1 engine.
3. **Non-Destructive Git Workflow**: Every milestone is an atomic Git commit. If anything goes wrong, `git reset` restores working state instantly.
4. **Thermal & Resource Watchdog**: Inference and training runs are executed with batch limits to ensure GPU temperatures remain safe on the laptop.
