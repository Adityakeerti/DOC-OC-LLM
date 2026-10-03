# DOC-OC v6 — Master Task Tracking

## 📅 Day 1: Foundation, Pipeline Architecture & Baseline Benchmarks
- [x] **Repository Reorganization**: Created clean modular directory structure (`api/`, `pipeline/`, `dataset/`, `benchmarks/`, `scripts/`, `results/`).
- [x] **Non-Destructive Preprocessing**: Implemented `pipeline/preprocess.py` (PyMuPDF PDF loading, EXIF auto-rotation, proportional Lanczos resizing).
- [x] **Zero-Shot VLM Client**: Implemented `pipeline/extract.py` communicating with local `llama-server`.
- [x] **Strict Pydantic Validation**: Implemented `pipeline/validate.py` with arithmetic cross-checks (`total == theory + practical`).
- [x] **Dataset Cataloging**: Cataloged 37 authentic Indian marksheets across CBSE, ICSE, UP, and Uttarakhand boards with `dataset/manifest.json`.
- [x] **Gold-Standard Ground Truth**: Hand-audited 10 gold-standard JSON files in `dataset/ground_truth/`.
- [x] **Empirical Baseline Benchmarks**: Logged 8-document test runs for both `Gemma-4-E2B` and `UI-TARS-7B-DPO`.
- [x] **Few-Shot Name Disambiguation Proof**: Tested `training/test_few_shot.py` on `12_3.jpg` — successfully resolved candidate name vs. parent name ambiguity.

---

## 🚀 Day 2: Advanced ML Systems Engineering & Optimization

### Phase 1: High-Performance Engine & Constrained Decoding (Speed + 100% Accuracy)
- [ ] **Task 1.1: 100% GPU Offload Configuration**
  - Update `start_server.sh` to offload all layers (`GPU_LAYERS=35` for Gemma, `GPU_LAYERS=36` for Qwen2.5-VL-3B).
  - Add native support for launching `Qwen2.5-VL-3B-Instruct` in `start_server.sh`.
- [ ] **Task 1.2: GBNF Grammar Constrained Decoding**
  - Create GBNF grammar specification matching the Pydantic schema in `pipeline/validate.py`.
  - Pass the grammar to `llama-server` during extraction to physically eliminate syntax errors, markdown wrappers, and leading zeros.
- [ ] **Task 1.3: Pipeline Prompt & Resolution Optimization**
  - Embed layout disambiguation rules directly into `pipeline/extract.py`.
  - Tune preprocessing dimension to optimal 1200px.
- [ ] **Task 1.4: Empirical Phase 1 Benchmark (Gemma vs. Qwen-3B Shootout)**
  - Benchmark both models across test marksheets.
  - Measure Time-To-First-Token (TTFT), tokens/sec, extraction time, and accuracy.
  - Save full benchmark log to `results/result_phase1_engine.txt`.
- [ ] **Task 1.5: Git Commit & Sync**
  - Commit Phase 1 code, scripts, and logs to `main` branch on `https://github.com/Adityakeerti/DOC-OC-LLM`.

---

### Phase 2: Architectural Adaptation & Model Surgery

#### Path A: Multimodal Fine-Tuning Setup
- [ ] **Task 2.1: Dataset Formatting**
  - Convert `dataset/manifest.json` and `dataset/ground_truth/` into multimodal ShareGPT / LLaVA conversation JSONL.
  - Split into 25 training, 6 validation, 6 test samples.
- [ ] **Task 2.2: QLoRA Adapter Training Pipeline**
  - Configure target modules (`q_proj`, `v_proj`, `k_proj`, `o_proj`, `mm_projector`).
  - Set rank $r=16, \alpha=32$ with label masking on response tokens.
  - Train adapter on RTX 4050 (under 5GB VRAM footprint).
- [ ] **Task 2.3: Evaluation & Validation**
  - Benchmark fine-tuned adapter against base model on the 6 test marksheets.
  - Record latency and accuracy changes in `results/result_finetune_lora.txt`.

#### Path B: Model Pruning Experiment (Depth Shrinking)
- [ ] **Task 2.4: Safety Backup**
  - Create verified bit-for-bit backup of model weights in `/home/aditya/AI/models/backups/`.
- [ ] **Task 2.5: Layer Redundancy Profiling**
  - Measure layer-to-layer cosine similarity / angular distance across transformer blocks using calibration marksheets.
- [ ] **Task 2.6: Layer Excision (GGUF Surgery)**
  - Excise 4–6 redundant middle blocks, update block count metadata, and save as pruned model checkpoint.
- [ ] **Task 2.7: Pruned Model Evaluation**
  - Benchmark pruned model vs. original model: measure latency decrease, memory footprint drop, and accuracy retention.
  - Save report to `results/result_pruning_experiment.txt`.

---

## 📊 Phase 3: Final Synthesis, Portfolio Matrix & GitHub Sync
- [ ] **Task 3.1**: Build Master Comparison Matrix (Base Gemma vs. Phase 1 Gemma vs. Qwen2.5-VL-3B vs. Fine-Tuned vs. Pruned).
- [ ] **Task 3.2**: Update `README.md` and project documentation with performance benchmarks.
- [ ] **Task 3.3**: Final Git commit and push to `https://github.com/Adityakeerti/DOC-OC-LLM`.
