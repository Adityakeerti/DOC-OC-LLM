# 📚 DOC-OC v6 — Documentation Index

Welcome to the internal engineering documentation for **DOC-OC v6**, a production-grade, local Vision-Language Model marksheet and certificate extraction engine built for sub-second, zero-cost, privacy-first inference on consumer GPUs (NVIDIA RTX 4050 6GB).

---

## 🗂️ Documentation Directory

| Document | Purpose | Key Topics Covered |
| :--- | :--- | :--- |
| **[`process.md`](./process.md)** | **Engineering Decision Log & Interview Prep** | Chronological record of all 12+ architectural breakthroughs, benchmark comparisons (UI-TARS vs Gemma vs Qwen), C++ GBNF grammar constrained decoding, Lanczos 1200px scaling, ShortGPT layer profiling, and self-healing validators. |
| **[`plan.md`](./plan.md)** | **Master Architectural Plan & Roadmap** | Hardware resource constraints (VRAM breakdown), modular pipeline design (preprocess → extract → validate), Phase 1 runtime optimizations, and Phase 2 fine-tuning / adapter roadmaps. |
| **[`tasks.md`](./tasks.md)** | **Sprint & Milestone Checklist** | Granular task-by-task status tracking across dataset collection, pipeline engineering, benchmark runs, and documentation syncs. |
| **[`prompt.md`](./prompt.md)** | **Prompt Engineering & Layout Grounding** | VLM system prompt design, layout disambiguation rules (`SUB. CODE` vs marks, candidate name vs parent name), and zero-shot vs few-shot prompt templates. |
| **[`day2-night-auto.md`](./day2-night-auto.md)** | **Autonomous Execution & Night Ops Guide** | Playbook for unattended batch evaluation, dataset compilation, layer redundancy analysis, and background process management. |
| **[`post.md`](./post.md)** | **LinkedIn & Public Announcement Drafts** | Ready-to-publish technical write-ups detailing the evolution from legacy DOC-OC pipelines to the local VLM engine. |

---

## 🎯 Recommended Reading Paths

### 1. For Technical Interviews & System Design Review
1. Start with the root [**`README.md`**](../README.md) for the high-level executive summary and benchmark comparison table.
2. Read [**`docs/process.md`**](./process.md) to dive deep into every real-world engineering challenge faced, why specific approaches were chosen over cloud OCR/heuristics, and the exact trade-offs made.
3. Review [**`docs/plan.md`**](./plan.md) to see how the system was modeled from hardware constraints up to production deployment.

### 2. For Deployment & Inference Developers
1. Review [**`docs/prompt.md`**](./prompt.md) to understand GBNF grammar constraints and layout parsing rules.
2. Check [**`docs/tasks.md`**](./tasks.md) to track current project status and remaining milestones.
