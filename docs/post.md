# 🚀 LinkedIn Post: The Evolution of DOC-OC (From Brittle Cascades to Local VLM Engine)

*Below are two LinkedIn post options engineered for high technical engagement. Option 1 is concise, punchy, and formatted specifically for the LinkedIn algorithm. Option 2 is a deep-dive systems breakdown.*

---

## 📌 Option 1: High-Signal Technical Story (Recommended)

```text
Stop building 10-stage OCR cascades. 

For the past versions of DOC-OC (v1–v5), our document extraction architecture looked like what most teams still deploy today:
→ Canny edge detection & OpenCV contour cropping
→ YOLO models for board logo detection
→ TableTransformers for cell slicing
→ Paid Cloud OCR APIs ($0.02 - $0.05 / page)
→ Hundreds of brittle regex rules that broke every time CBSE or UP Board changed a border color or layout.

It was slow, expensive, and broke on edge cases.

For DOC-OC v6, I completely rebuilt the engine from scratch around local Vision-Language Models (VLMs) running 100% offline on a consumer laptop GPU (RTX 4050, 6GB VRAM). 

Zero cloud APIs. Zero cost per page. Zero regex.

Here is the real ML systems engineering behind making a local VLM production-ready:

1. Latency Drop: 27.12s ➔ 6.28s (4.32x Speedup)
Modern reasoning models (like Gemma-4) default to generating internal thought chains (~1,500 conversational tokens) before emitting structured data. By configuring the inference runtime with reasoning suppressed (`--reasoning off`, `--reasoning-budget 0`), extraction time dropped from 27 seconds down to 6.28s (single docs down to 4.24s) at 83 tok/s.

2. C++ GBNF Constrained Decoding (Eliminating Hallucinations)
Instead of asking the LLM to "please output valid JSON" and praying it doesn't emit markdown wrappers or octal leading zeros, we compile our Pydantic schema into a strict GBNF grammar passed directly to llama.cpp's C++ sampler. The sampler masks illegal token logits during generation. Syntax invalidity is mathematically impossible.

3. Visual Patch Optimization (43% Fewer Tokens)
Document micro-text needs sharpness, not bloated resolutions. Using proportional 1200px Lanczos resampling, we preserved high-frequency character edges while slashing visual patch tokens by 43%, dramatically accelerating Time-to-First-Token (TTFT).

4. ShortGPT Layer Redundancy Profiling
We ran layer-to-layer cosine similarity and angular distance profiling across all 35 transformer blocks to investigate weight pruning. We discovered peak redundancy at Blocks 14 & 15 (Cosine Sim 0.8953), but also uncovered architectural guardrails: Gemma-4's Per-Layer Embeddings (PLE) span across all layers in unified matrices. Understanding the underlying model architecture saved us from unstable weight slicing when runtime optimizations were already exceeding our latency budget.

5. Self-Healing Arithmetic Reconciliation
LLMs are vision engines, not arithmetic calculators. A lightweight post-processor cross-checks component marks (Theory + Practical == Total) and auto-reconciles table misalignments with zero human intervention.

📊 The Results on Authentic Multi-Board Marksheets:
• Latency: 6.28s average on consumer edge hardware
• Schema Adherence: 100.0% (GBNF locked)
• Candidate Name & Marks Precision: 100.0%
• Cloud API bill: $0.00

Building with AI isn't just about calling API endpoints — it's about systems engineering, constrained decoding, and memory-aware runtime optimization.

Open-source code, benchmarks, and technical logs:
👉 https://github.com/Adityakeerti/DOC-OC-LLM

#MachineLearning #LLM #VLM #ComputerVision #EdgeAI #SystemsEngineering #OpenSource #Python #CUDA
```

---

## 📌 Option 2: Deep Systems / Low-Level Breakdown

```text
How we achieved 6.28s edge VLM inference with 100% schema accuracy on a 6GB laptop GPU:

Most document AI pipelines in production are fragile pipelines of OpenCV heuristics, paid cloud OCR, and regex. 

In DOC-OC v6, we replaced the legacy cascade with an end-to-end multimodal pipeline powered by Gemma-4-E2B. But deploying a VLM locally comes with steep systems challenges: VRAM limits, high latency, and output hallucination.

Here is how we solved them at the engine level:

🔹 Constrained Decoding via GBNF Grammars
Prompt engineering alone cannot guarantee JSON compliance. By passing our Pydantic schema as a Context-Free Grammar (GBNF) directly to llama.cpp's C++ decoding loop, we enforce logit masking at each sampling step. The model literally cannot sample an invalid syntax token or octal character.

🔹 Reasoning Budget Suppression
Gemma 4 was initially clocking 27+ seconds per document. Profiling revealed that >70% of wall-clock time was spent generating ~1,500 internal reasoning tokens before producing the JSON payload. By disabling reasoning traces at the server runtime, we achieved an immediate 4.3x speedup down to 6.28s.

🔹 Spatial Visual Grounding
Multi-board Indian marksheets have complex 2D column layouts (e.g. CBSE's SUB. CODE vs THEORY vs TOTAL, and bilingual Hindi/English headers). Rather than brittle OCR bounding boxes, we grounded attention coordinates directly in the multimodal prompt, resolving parent vs. candidate name confusions.

🔹 ShortGPT Profiling & PLE Architecture
We profiled block redundancy using ShortGPT cosine similarity across all 35 transformer blocks. Peak redundancy occurred at layers 14 & 15 (Angular Dist 0.1470). However, deep tensor analysis revealed Gemma-4's Per-Layer Embeddings (PLE) unified tensor design, illustrating the exact trade-offs between pruning vs. runtime optimization on quantized weights.

Architecture:
• Engine: llama.cpp (100% CUDA offload, FlashAttention enabled)
• Service: FastAPI + Split-Screen Verification UI
• Hardware: NVIDIA RTX 4050 Laptop GPU (3.2 GB / 6 GB VRAM)
• Privacy: 100% offline, zero cloud calls

All source code, technical interview logs, and benchmark logs are public on GitHub:
👉 https://github.com/Adityakeerti/DOC-OC-LLM

#DeepLearning #MLOps #LLMOps #CUDA #llama_cpp #VisionLanguageModels #ArtificialIntelligence
```
