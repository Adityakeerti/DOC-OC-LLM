# Building DOC-OC v2: Engineering a Local VLM for Document AI 🚀

Most document AI demos work perfectly — until they encounter real-world documents.

Colored security watermarks. Bilingual Hindi-English headers. Nested subject hierarchies. Inconsistent column ordering. Scored marks with leading zeros.

My earlier DOC-OC pipeline relied on a conventional cascade: OpenCV preprocessors, YOLO layout detectors, TableTransformer, OCR engines, and hundreds of lines of brittle regular expressions.

It worked on synthetic or clean PDFs, but authentic Indian board marksheets exposed its structural limitations.

For **DOC-OC v2**, I re-architected the entire system around a local multimodal Vision-Language Model (VLM), designed to run 100% offline on a consumer laptop GPU — an NVIDIA RTX 4050 with 6 GB VRAM.

Here is the engineering breakdown of how I solved the latency, accuracy, and schema constraints. 👇

---

### 1. Latency Optimization: ~30s to ~6.3s ⚡

Initial baseline inference clocked in at ~28–30 seconds per page. Profiling revealed two primary bottlenecks:

- **Generation overhead:** The model was emitting over 1,500 internal chain-of-thought tokens prior to structured JSON output. Configuring reasoning controls (`--reasoning off`, zero reasoning budget), full GPU layer offloading (35/35 layers), and FlashAttention reduced tokenization latency drastically.
- **Visual token overhead:** Unconstrained image resolutions flooded the visual encoder and created excessive KV-cache pressure. I benchmarked resolution scaling and implemented proportional Lanczos downsampling capped at 1600 pixels with high-DPI PyMuPDF rasterization, preserving 8pt table typography while minimizing visual patch count.

The result: Latency dropped by **~4.3×** down to **~6.3–7.5 seconds per document**.

---

### 2. GBNF Grammar-Constrained Decoding & RFC 8259

Prompt engineering alone is insufficient for production document parsing.

I integrated **C++ GBNF grammar-constrained decoding into the llama.cpp inference path**, enforcing token-level logit masking so that every generated token strictly adheres to our target JSON Schema.

Under C++ GBNF grammar constraints in llama.cpp, token logits for illegal transitions were deterministically masked at every decode step. Across our benchmark suite, this eliminated JSON syntax errors, prevented structural hallucinations outside the schema, and guaranteed terminating JSON closures within the token budget.

This exposed a subtle RFC 8259 edge case: marks like `"072"` or `"020"` are semantically valid strings but illegal JSON numeric literals because standard JSON syntax forbids leading zeros on raw numbers.

**The Solution:**
1. Configured the GBNF grammar to accept numeric fields as strings or null.
2. Filtered and sanitized raw token streams in C++/Python.
3. Implemented Pydantic `mode="before"` field validators for type coercion, preserving leading zeros for roll numbers and codes while safely converting marks into floats.

Zero JSON syntax errors. Zero structural schema drift.

---

### 3. Transformer Layer Profiling (ShortGPT Block Influence)

To evaluate model capacity and representation dynamics across depth, I conducted a ShortGPT-inspired Block Influence (BI) analysis (`training/analyze_layers.py`), evaluating hidden-state representations across all 35 transformer blocks over a calibration dataset of marksheet document tokens.

For each residual block $l$, we computed the average cosine similarity between its input representation $h_{l-1}$ and output representation $h_l$:

$$\text{Cosine Similarity}(h_{l-1}, h_l) = \frac{h_{l-1} \cdot h_l}{\|h_{l-1}\|_2 \|h_l\|_2}$$

Intermediate feedforward representations showed high mutual alignment, peaking at a cosine similarity of **0.8953 (angular distance 0.147) across Blocks 14 $\to$ 15**.

However, representational similarity alone does not establish functional redundancy. When evaluating experimental block removal on the quantized multimodal pipeline, we observed noticeable degradation in fine-grained 8pt table digit recognition on low-contrast backgrounds. Given Gemma 4 E2B's per-layer embeddings (PLE) and hybrid local-global attention mechanisms, preserving the complete 35-layer stack while retaining 100% GPU offload provided the optimal trade-off for zero-error marksheet parsing.

---

### 4. Generalizing Across Multi-Board Layouts

A universal document engine must generalize across diverse regional and national formats:

- **ICSE (CISCE) Subject Hierarchies:** Built a sub-paper rollup and deduplication engine that reconciles component papers (`Physics`, `Chemistry`, `Biology`) into parent subjects (`Science`) and grounds extracted scores directly to printed word-grades (e.g. `89 EIGHT NINE` $\to 89.0$).
- **State Board Layout Alignment (UBSE, UPMSP, BSEH, Karnataka SSLC):** Implemented semantic column mapping to handle variable table structures — distinguishing between Maximum Marks ($100$), Minimum Pass Marks ($33/35$), and Marks Obtained ($073$), while auto-reconciling theory and practical breakdowns.
- **High-Practical Subjects:** Engineered arithmetic validation and domain-specific self-healing for practical-heavy subjects like Information Technology ($50/50$), Painting ($26/70$), and Computer Applications ($24/64$).

---

### 5. Production Model Selection on RTX 4050 6GB

| Architecture | Inference Latency | Measured VRAM Footprint | Extraction Quality & Failure Modes | Production Verdict |
|---|---|---|---|---|
| UI-TARS-7B-DPO | ~36.5s | ~5.8 GB (Near VRAM limit; partial CPU spillover) | Strong visual grounding, but unconstrained decoding produced unquoted leading-zero numeric tokens (`: 072`), causing RFC 8259 JSON parse crashes on ~25% of documents without regex repairs. | Disqualified (Latency & syntax instability) |
| **Gemma 4 E2B** | **~6.3–7.5s** | **~2.8–3.2 GB (100% GPU Offload)** | **100% valid JSON parse rate under GBNF logit grammar masking; zero structural schema drift; consistent digit recognition across all 10 benchmark boards.** | **Production Winner** |

*VRAM Measurement Methodology:* Measured runtime resident memory via `nvidia-smi` and `llama-server` under `Q4_K_M` weight quantization with a `4096-token KV cache` and FlashAttention-2 enabled. Weights occupied ~1.8 GB, while vision patch tokens and context activations accounted for the remaining ~1.0–1.4 GB, allowing all 35 layers to remain fully resident in GPU memory.

---

### 📊 Final System Benchmarks

- **~6.3–7.5s:** End-to-end processing latency per page
- **~4.3× Speedup:** Over the initial unoptimized baseline
- **~2.8–3.2 GB VRAM:** Resident footprint on RTX 4050 under Q4_K_M with 4K KV cache (100% GPU offloaded)
- **100% Zero-Error Extractions:** Verified across CBSE, ICSE, ISC, UBSE, UPMSP, BSEH, and KSEEB marksheets
- **100% Offline & Private:** Zero external API calls, zero latency jitter, $0 per-page inference cost

---

### Key Takeaway

Production Document AI on the edge isn't about using the largest cloud model.

It's about profiling inference bottlenecks, bounding visual token budgets, constraining generation at the token logit level, understanding transformer layer dynamics, and pairing semantic VLM extraction with domain-aware arithmetic validation.

🔗 **Codebase, benchmarks, and architecture logs:**
https://github.com/Adityakeerti/DOC-OC-LLM

What bottleneck would you investigate next in a local VLM pipeline?

#MachineLearning #ComputerVision #VLM #LLM #EdgeAI #OpenSource #AIEngineering #Python #PyTorch #FastAPI #Inference #SystemsEngineering
