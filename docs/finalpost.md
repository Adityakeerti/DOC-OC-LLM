# Building DOC-OC v2: Engineering a Local VLM for Document AI 🚀

Most document AI demos work perfectly — until they encounter real-world documents.

Colored security backgrounds. Bilingual Hindi-English headers. Nested subject tables. Inconsistent column ordering. Marks with leading zeros.

My earlier DOC-OC versions relied on a conventional pipeline: OpenCV, YOLO, TableTransformer, OCR engines, and hundreds of lines of regular expressions.

It worked on clean PDFs, but authentic Indian state board marksheets exposed its limitations.

For **DOC-OC v2**, I re-architected the system around a local multimodal Vision-Language Model (VLM), designed to run offline on a consumer laptop GPU — my RTX 4050 with 6 GB VRAM.

Here's how I approached the engineering challenges. 👇

---

### 1. Inference: ~30s to ~6.3s ⚡

Initial inference took approximately 28–30 seconds per page. Profiling revealed two major bottlenecks.

- **Generation overhead:** Over 1,500 internal reasoning tokens were generated before structured output. Configuring reasoning controls, full GPU offloading, and FlashAttention substantially reduced latency.
- **Visual token overhead:** Excessive image resolution increased visual processing and KV-cache pressure. I benchmarked resolutions and implemented proportional Lanczos downsampling capped at 1280 pixels, using PyMuPDF for PDF rendering.

The goal was to reduce computation while preserving critical details like 8pt text, interior zeros, and tightly packed table cells.

### 2. Constrained JSON Generation

Prompt engineering alone couldn't guarantee reliable structured output.

I integrated **GBNF grammar-constrained decoding into the llama.cpp inference path**, using token-level logit masking to restrict generation to grammar-compliant output.

This exposed a subtle issue: marks such as `"072"` and `"020"` are valid strings but invalid JSON number literals because standard JSON syntax prohibits leading zeros.

The fix was to allow numeric fields to accept strings or null, then normalize values through Pydantic's `mode="before"` validation.

The result: constrained generation combined with application-level validation, without losing marks containing leading zeros.

### 3. Transformer Layer Analysis

I implemented a ShortGPT-inspired Block Influence analysis in `training/analyze_layers.py`, examining hidden-state similarity across all 35 transformer blocks.

Middle layers showed higher cosine similarity, peaking at **0.8953 around Blocks 14–15**.

However, similarity doesn't automatically mean a layer can be removed safely. After examining Gemma 4 E2B's tensor layout, per-layer embeddings, and hybrid attention architecture, I decided against structural pruning.

With runtime optimization already delivering substantial improvements, preserving architectural stability was the better trade-off.

### 4. Generalizing Across Board Formats

A universal document engine cannot depend on one board's layout.

I addressed three recurring challenges:

- **ICSE subject hierarchies:** Built a sub-paper rollup mechanism for aggregate subjects such as Science and H.C.G. alongside Physics, Chemistry, and Biology, reconciling results with printed percentage-in-words fields.
- **Dynamic columns:** Reworked extraction around semantic column roles and added arithmetic validation to detect and correct shifts involving maximum marks, pass marks, and marks obtained.
- **Practical-heavy subjects:** Expanded practical-mark handling to cover IT, Painting, Vocational Studies, and Computer Applications.

The objective was to combine semantic extraction with domain-specific validation rather than rely on fixed positional rules.

### 5. Model Selection & Benchmarks on RTX 4050 6GB

I evaluated local VLM architectures across authentic CBSE, ICSE, ISC, UPMSP, BSEH Haryana, and UBSE Uttarakhand formats.

| Model | Observed results |
|---|---|
| UI-TARS-7B-DPO | ~36.5s; heavy memory footprint requiring CPU offloading on 6GB VRAM |
| **Gemma 4 E2B** | **~6.3s; 100% GPU offload (35 layers), seamless GBNF compilation, and ultra-fast deterministic JSON** |

**Gemma 4 E2B emerged as the clear production choice.**

Its tokenizer and chat template compile cleanly into C++ GBNF grammars without runaway generation loops, and it fits 100% inside ~2.8 GB VRAM with instant sub-7s response times.

### 📊 Final Results

- **~6.3s:** Average warm inference latency per document
- **~4.3× speedup:** Compared with the original ~28–30s baseline
- **~2.8 GB VRAM:** Lightweight footprint on RTX 4050 (100% GPU offload)
- **100% schema validity:** Deterministic GBNF logit masking + Pydantic validation
- **Format-agnostic:** Robust extraction across national and regional Indian board layouts
- **Privacy and cost:** 100% local processing with $0 per-page cloud inference cost

### The Takeaway

Production document AI isn't just about choosing a massive model.

It's about profiling inference, controlling visual token budgets, constraining generation at the logit level, understanding model architecture, and validating outputs against real-world domain rules.

That's what I've been building with **DOC-OC v2** — a fast, lightweight local document intelligence engine running on consumer hardware.

🔗 **Codebase, benchmarks, and architecture logs:**

https://github.com/Adityakeerti/DOC-OC-LLM

What bottleneck would you investigate next in a local VLM pipeline?

#MachineLearning #ComputerVision #VLM #LLM #EdgeAI #OpenSource #AIEngineering #Python #PyTorch #FastAPI #Inference #SystemsEngineering
