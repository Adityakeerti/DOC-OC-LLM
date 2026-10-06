I rebuilt DOC-OC around a local Vision-Language Model.

Earlier versions of the project relied on a traditional document-extraction pipeline:

→ OpenCV preprocessing and cropping
→ YOLO-based document/region detection
→ Table extraction
→ OCR
→ Regex and rule-based post-processing

It worked, but the pipeline became increasingly brittle as document layouts changed across boards and document formats.

For DOC-OC V2, I moved the core extraction step to a local VLM running entirely on a consumer GPU.

The goal was simple: reduce latency while making the extraction pipeline more robust across different document layouts.

### What I worked on

**1. Inference optimization**

The initial VLM implementation was taking around 27–30 seconds per document.

Profiling the inference path revealed that the model was spending the vast majority of its time generating internal reasoning traces (>1,500 conversational tokens) before emitting structured data. For an extraction task, this is pure latency overhead.

By suppressing reasoning tokens (`--reasoning-budget 0` in llama.cpp), offloading all transformer layers to the GPU, and enabling FlashAttention, warm inference dropped down to ~6.3s per page on an RTX 4050 6GB.

**2. Constrained structured generation (C++ GBNF)**

A VLM can visually parse a document correctly and still produce an invalid JSON response—emitting markdown wrappers, trailing commas, or numbers with leading zeros (e.g. `077`) that break standard JSON parsers as illegal octals.

Instead of relying on prompt engineering and hoping the model complies, I integrated formal GBNF (GGML BNF) grammar constraints directly into llama.cpp.

During autoregressive generation, the sampler evaluates the grammar's state machine and applies logit masking at each decoding step. Any token that would violate valid JSON syntax or our defined schema has its probability forced to zero before sampling. This moves structural reliability from prompt engineering directly into the C++ decoding loop.

**3. Visual token optimization**

Image resolution dictates the visual token count passed into the multimodal projector, which directly impacts Time-to-First-Token (TTFT) and memory bandwidth.

Passing full-resolution scans generated an excessive number of visual patch tokens without yielding additional OCR accuracy.

I benchmarked multiple resolutions and applied proportional Lanczos downsampling capped at 1200px. This preserved high-frequency character edges and micro-text on watermarked marksheets while reducing visual tokens by ~43%, significantly cutting prefill time without information loss.

**4. Model architecture & ShortGPT redundancy analysis**

To investigate whether model compression could reduce inference cost further, I implemented ShortGPT's Block Influence (BI) metric, measuring layer-to-layer cosine similarity and angular distance across all 35 transformer blocks.

The analysis revealed significant representation redundancy in the middle layers, peaking at blocks 14 and 15 (cosine similarity 0.895, angular distance 0.147).

However, inspecting the tensor layout before pruning revealed critical architectural constraints: Gemma uses Per-Layer Embeddings (PLE) across layers in unified matrices (`per_layer_token_embd.weight`) alongside shared sliding-window KV attention heads. Pruning middle blocks risks breaking tensor indexing and KV-cache alignment in quantized formats.

Given that runtime optimizations had already brought latency down to ~6.3s, keeping the base architecture intact avoided destabilizing the quantized weights for marginal gain.

### Current result

~27–30s → ~6.3s warm inference
RTX 4050 6GB (~3.2 GB VRAM consumed)
Fully local / offline inference
100% schema validity via GBNF constrained decoding
No per-page cloud OCR cost

What I've found most interesting is that getting a VLM to work is only the beginning.

A large part of the engineering is in profiling the inference path, controlling decoding at the logit level, managing visual token budgets, and understanding what the model and runtime are actually doing underneath.

Code, benchmarks, and engineering logs:
https://github.com/Adityakeerti/DOC-OC-LLM

#MachineLearning #VLM #LLM #ComputerVision #EdgeAI #CUDA #OpenSource #AIEngineering
