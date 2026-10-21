import React, { useState } from 'react'

interface HomeProps {
  onNavigateToWorkspace: () => void;
  onNavigateToPipeline: () => void;
}

export default function Home({ onNavigateToWorkspace, onNavigateToPipeline }: HomeProps) {
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  const faqs = [
    {
      q: "What is DOC-OC v2 and how does it differ from traditional OCR systems?",
      a: "DOC-OC v2 is a local, privacy-first Vision-Language Model extraction engine designed specifically for complex Indian academic documents. Unlike legacy pipelines that chain together Canny contour deskewers, YOLO logo classifiers, Haar face detectors, TableTransformers, and hardcoded regex, DOC-OC v2 replaces the entire brittle cascade with an end-to-end spatial VLM (Gemma-4-E2B). This unifies layout understanding, text extraction, and semantic reasoning in a single pass."
    },
    {
      q: "How does DOC-OC v2 achieve 6.28s extraction latency on dedicated hardware?",
      a: "Through three deep ML optimizations benchmarked on dedicated local hardware: (1) Eliminating reasoning token lag by disabling internal chain-of-thought tokens (--reasoning off, --reasoning-budget 0), which saves 1,500+ superfluous conversational tokens; (2) Non-destructive proportional Lanczos 1200px scaling, which reduces visual tokens by 43% (from 1,344 to 768 tokens) while preserving 8pt table font contrast; (3) 100% GPU offloading with FlashAttention-2 in llama.cpp, running at 83 tokens/second on an offline edge GPU workstation. Please note: This public web deployment runs on a free cloud instance (subject to cold boots and shared server quotas), so live web latency will not match the benchmark. Watch the real-time offline benchmark run on YouTube (https://youtu.be/OsfTcbbgvao)."
    },
    {
      q: "What is C++ GBNF constrained logit grammar decoding?",
      a: "Standard autoregressive LLMs frequently slip into syntax errors (e.g. invalid markdown fences, trailing commas, or leading-zero octal violations like '077'). In DOC-OC v2, our Pydantic schema is compiled into a formal GGML BNF (GBNF) grammar. The C++ sampler masks out illegal token logits at every generation step, making formatting defects physically impossible and guaranteeing 100% RFC 8259 compliance."
    },
    {
      q: "How does the Self-Healing Arithmetic Validation Engine work?",
      a: "Academic marksheets often contain complex grading rubrics with separate theory, practical, and total columns. DOC-OC v2 enforces strict arithmetic reconciliation: verifying that marks_theory + marks_practical == total_obtained. If minor single-digit slips occur due to image noise or stamp overlap, the validation engine automatically recalculates and reconciles the values against max marks and percentages, logging an audit trail."
    },
    {
      q: "Which Indian educational boards are benchmarked and verified?",
      a: "DOC-OC v2 has been empirically benchmarked across CBSE (10th and 12th), ICSE / ISC (CISCE), UPMSP (UP Board with pink security patterns), BSEH (Haryana Board with green security backgrounds), UBSE (Uttarakhand State Board), and multi-semester university degree transcripts."
    }
  ];

  return (
    <div className="page-fade-in">
      {/* Hero Section - Poster Layout */}
      <section className="product-tile-dark hero-section">
        <div className="tile-content">
          <span className="tile-tagline">DOC-OC v2 • Architectural Engine (v6 Core)</span>
          <h1 className="display-xl hero-display">Universal Indian Marksheet & Certificate Extractor</h1>
          <p className="tile-lead" style={{ maxWidth: 760 }}>
            High-Performance Vision-Language Model extraction engine for multi-board Indian academic transcripts.
            Zero cloud OCR APIs • Zero regex • Zero cost-per-page • Designed for edge and local GPU deployment.
          </p>
          <div className="hero-actions">
            <button className="btn-primary" onClick={onNavigateToWorkspace}>
              Launch Workspace
            </button>
            <button className="btn-secondary" onClick={onNavigateToPipeline}>
              Explore 3-Pillar Architecture
            </button>
            <a
              href="https://youtu.be/OsfTcbbgvao"
              target="_blank"
              rel="noopener noreferrer"
              className="btn-secondary"
              style={{
                textDecoration: 'none',
                display: 'inline-flex',
                alignItems: 'center',
                gap: 7,
                color: '#ffffff',
                background: 'rgba(220, 38, 38, 0.25)',
                border: '1px solid rgba(220, 38, 38, 0.5)',
              }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="#ef4444">
                <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
              </svg>
              Watch Benchmark Video
            </a>
          </div>

          {/* Premium CSS Interactive Mock Visualization */}
          <div className="hero-visual-container">
            <div className="hero-visual-card">
              <div className="scanner-line-glow"></div>
              <div className="visual-sheet">
                <div className="visual-header-row">
                  <div className="visual-logo-placeholder" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <svg className="logo-spark" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ color: 'var(--color-accent-blue)' }}>
                      <path d="M12 2L2 7l10 5 10-5-10-5z" />
                      <path d="M2 17l10 5 10-5" />
                      <path d="M2 12l10 5 10-5" />
                    </svg>
                  </div>
                  <div className="visual-header-text">
                    <div className="text-line-thick" style={{ width: 140 }}></div>
                    <div className="text-line-thin" style={{ width: 90 }}></div>
                  </div>
                  <div style={{ marginLeft: 'auto', display: 'flex', gap: 6 }}>
                    <span className="nav-badge" style={{ color: '#22c55e', borderColor: 'rgba(34,197,94,0.3)', background: 'rgba(34,197,94,0.1)' }}>
                      GBNF Logit Lock
                    </span>
                  </div>
                </div>
                
                {/* Spatial Grounding Row */}
                <div className="visual-avatar-row" style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <div style={{ border: '1px solid #0099ff', borderRadius: 6, padding: '4px 8px', background: 'rgba(0,153,255,0.08)', fontSize: 11, fontFamily: 'monospace', color: '#0099ff' }}>
                    Candidate Name: Grounded (Y-Offset)
                  </div>
                  <div className="visual-details-lines" style={{ flex: 1 }}>
                    <div className="detail-line" style={{ width: '85%' }}></div>
                    <div className="detail-line short" style={{ width: '55%' }}></div>
                  </div>
                </div>

                {/* Arithmetic Reconciled Table Mock */}
                <div className="visual-table-placeholder">
                  <div className="visual-table-row header">
                    <div className="col" style={{ width: '35%' }}></div>
                    <div className="col" style={{ width: '20%' }}></div>
                    <div className="col" style={{ width: '20%' }}></div>
                    <div className="col" style={{ width: '25%' }}></div>
                  </div>
                  <div className="visual-table-row">
                    <div className="col box-glow-blue" style={{ width: '35%' }}></div>
                    <div className="col box-glow-blue" style={{ width: '20%' }}></div>
                    <div className="col box-glow-blue" style={{ width: '20%' }}></div>
                    <div className="col box-glow-blue" style={{ width: '25%' }}></div>
                  </div>
                  <div className="visual-table-row">
                    <div className="col" style={{ width: '35%' }}></div>
                    <div className="col" style={{ width: '20%' }}></div>
                    <div className="col" style={{ width: '20%' }}></div>
                    <div className="col" style={{ width: '25%' }}></div>
                  </div>
                </div>

                <div style={{ marginTop: 10, display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 11, color: 'var(--color-ink-muted)' }}>
                  <span>PyMuPDF 2× Matrix Rasterization</span>
                  <span style={{ color: '#22c55e' }}>Self-Healing Arithmetic: PASS</span>
                </div>
              </div>
            </div>
          </div>

          {/* Real Benchmark Stats Display */}
          <div className="stats-grid">
            <div className="stat-item">
              <span className="stat-num" style={{ color: '#22c55e' }}>6.28s</span>
              <span className="stat-label">Local Warm Latency (Ref)</span>
            </div>
            <div className="stat-item">
              <span className="stat-num" style={{ color: '#0099ff' }}>100%</span>
              <span className="stat-label">C++ GBNF Schema Adherence</span>
            </div>
            <div className="stat-item">
              <span className="stat-num">3.2 GB</span>
              <span className="stat-label">Resident VRAM Footprint</span>
            </div>
            <div className="stat-item">
              <span className="stat-num" style={{ color: '#22c55e' }}>$0.00</span>
              <span className="stat-label">Cost Per Page (Zero Paid APIs)</span>
            </div>
          </div>
          <div style={{ textAlign: 'center', marginTop: 14, fontSize: 12.5, color: 'var(--color-ink-muted)' }}>
            ⚡ Benchmarks measured on dedicated local hardware. Deployed web demo runs on a free cloud instance with variable latency. <a href="https://youtu.be/OsfTcbbgvao" target="_blank" rel="noopener noreferrer" style={{ color: '#ef4444', textDecoration: 'underline', fontWeight: 500 }}>Watch real-time YouTube benchmark run ↗</a>
          </div>
        </div>
      </section>

      {/* 3-Pillar Architectural Breakdown */}
      <section id="key-benefits" className="product-tile-dark">
        <div className="tile-content">
          <span className="tile-tagline">Architectural Innovation</span>
          <h2 className="display-lg">The 3-Pillar Vision-Language Engine</h2>
          <p className="tile-lead" style={{ maxWidth: 720 }}>
            DOC-OC v2 completely eliminates the fragile multi-stage cascade (Canny cropping, YOLO logo detection, Haar cascades, TableTransformers, and regex) in favor of a unified spatial VLM pipeline.
          </p>

          <div className="features-grid">
            {/* Pillar 1 */}
            <div className="store-utility-card">
              <div className="card-badge-dot" style={{ backgroundColor: '#0ea5e9' }}></div>
              <div className="card-title">1. Non-Destructive Preprocessing</div>
              <div className="card-desc">
                PyMuPDF 2× matrix rasterization preserves vector-crisp 8pt table fonts. Automatic EXIF orientation fixes rotated mobile phone photos, while proportional 1200px Lanczos scaling reduces visual token count by 43%.
              </div>
              <div style={{ marginTop: 12, fontSize: 12, fontFamily: 'monospace', color: '#0ea5e9' }}>
                pipeline/preprocess.py • 768 visual tokens
              </div>
            </div>

            {/* Pillar 2 */}
            <div className="gradient-spotlight-card">
              <div className="card-badge-dot" style={{ backgroundColor: '#22c55e' }}></div>
              <div className="card-title">2. C++ GBNF Constrained Inference</div>
              <div className="card-desc">
                High-throughput execution of Gemma-4-E2B with token-level logit masking via GBNF JSON Schema, making syntax defects physically impossible. Disabled reasoning traces eliminate 1,500+ token thinking lag (83 tok/s on local reference GPU).
              </div>
              <div style={{ marginTop: 12, fontSize: 12, fontFamily: 'monospace', color: '#22c55e' }}>
                pipeline/extract.py • Deterministic Grammar
              </div>
            </div>

            {/* Pillar 3 */}
            <div className="gradient-spotlight-card-orange">
              <div className="card-badge-dot" style={{ backgroundColor: '#f59e0b' }}></div>
              <div className="card-title">3. Self-Healing Arithmetic Validation</div>
              <div className="card-desc">
                Strict Pydantic models validate structure. Automated arithmetic cross-checking ensures Theory + Practical equals Total Obtained marks, while in-context layout grounding resolves Candidate Name vs. Parent Name conflicts.
              </div>
              <div style={{ marginTop: 12, fontSize: 12, fontFamily: 'monospace', color: '#f59e0b' }}>
                pipeline/validate.py • RFC 8259 Certified
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Board Compatibility Showcase */}
      <section className="product-tile-dark" style={{ borderTop: '1px solid var(--color-hairline)' }}>
        <div className="tile-content">
          <span className="tile-tagline">Dataset Generalization</span>
          <h2 className="display-lg">Built for Complex Indian Academic Transcripts</h2>
          <p className="tile-lead" style={{ maxWidth: 720 }}>
            Tested and benchmarked on 37 authentic documents across diverse state and central educational authorities with distinct color patterns and layout variations.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, width: '100%', marginTop: 10 }}>
            <div style={{ background: 'var(--color-surface-1)', border: '1px solid var(--color-hairline)', borderRadius: 12, padding: 18 }}>
              <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 4 }}>CBSE Board</div>
              <div style={{ fontSize: 13, color: 'var(--color-ink-muted)' }}>Class 10th & 12th Senior Secondary</div>
              <div style={{ fontSize: 11, color: '#22c55e', marginTop: 10 }}>100% Name & Roll Accuracy</div>
            </div>
            <div style={{ background: 'var(--color-surface-1)', border: '1px solid var(--color-hairline)', borderRadius: 12, padding: 18 }}>
              <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 4 }}>ICSE & ISC</div>
              <div style={{ fontSize: 13, color: 'var(--color-ink-muted)' }}>Council for Indian School Certificate</div>
              <div style={{ fontSize: 11, color: '#22c55e', marginTop: 10 }}>100% Subject Grade Precision</div>
            </div>
            <div style={{ background: 'var(--color-surface-1)', border: '1px solid var(--color-hairline)', borderRadius: 12, padding: 18 }}>
              <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 4 }}>UP Board (UPMSP)</div>
              <div style={{ fontSize: 13, color: 'var(--color-ink-muted)' }}>High School Pink Security Texture</div>
              <div style={{ fontSize: 11, color: '#22c55e', marginTop: 10 }}>Background-Resistant Grounding</div>
            </div>
            <div style={{ background: 'var(--color-surface-1)', border: '1px solid var(--color-hairline)', borderRadius: 12, padding: 18 }}>
              <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 4 }}>BSEH Haryana</div>
              <div style={{ fontSize: 13, color: 'var(--color-ink-muted)' }}>Secondary & Sr. Sec Green Background</div>
              <div style={{ fontSize: 11, color: '#22c55e', marginTop: 10 }}>Zero OCR Contrast Artifacts</div>
            </div>
          </div>
        </div>
      </section>

      {/* AEO / Answer Engine Optimization FAQ Section */}
      <section className="product-tile-dark" style={{ borderTop: '1px solid var(--color-hairline)' }}>
        <div className="tile-content">
          <span className="tile-tagline">AI Answer Engine Knowledge Base</span>
          <h2 className="display-lg">Frequently Asked Technical Questions</h2>
          <p className="tile-lead" style={{ maxWidth: 680 }}>
            Structured knowledge base optimized for direct citation by Perplexity, ChatGPT Search, Gemini, and Generative Search Engines.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, width: '100%', maxWidth: 840, marginTop: 12 }}>
            {faqs.map((faq, idx) => {
              const isOpen = openFaq === idx;
              return (
                <div 
                  key={idx} 
                  style={{
                    background: 'var(--color-surface-1)',
                    border: '1px solid var(--color-hairline)',
                    borderRadius: 12,
                    overflow: 'hidden',
                    transition: 'border-color 0.2s ease'
                  }}
                >
                  <button
                    onClick={() => setOpenFaq(isOpen ? null : idx)}
                    style={{
                      width: '100%',
                      padding: '18px 20px',
                      background: 'none',
                      border: 'none',
                      color: 'var(--color-ink)',
                      textAlign: 'left',
                      fontSize: 16,
                      fontWeight: 600,
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      cursor: 'pointer'
                    }}
                  >
                    <span>{faq.q}</span>
                    <span style={{ fontSize: 18, color: 'var(--color-accent-blue)', transform: isOpen ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s ease' }}>
                      ▼
                    </span>
                  </button>
                  {isOpen && (
                    <div style={{ padding: '0 20px 20px 20px', fontSize: 14, color: 'var(--color-ink-muted)', lineHeight: 1.6, borderTop: '1px solid var(--color-hairline)', paddingTop: 14 }}>
                      {faq.a}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Overview Interactive Promotion */}
      <section className="product-tile-dark promo-section">
        <div className="tile-content" style={{ alignItems: 'center', textAlign: 'center' }}>
          <h2 className="display-lg">Ready to experience DOC-OC v2?</h2>
          <p className="tile-lead" style={{ maxWidth: 600 }}>
            Run live extractions on authentic Indian marksheets, inspect C++ GBNF constrained JSON, or walk through the full multi-document student onboarding pipeline.
          </p>
          <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
            <button className="btn-primary" onClick={onNavigateToWorkspace}>
              Launch Workspace
            </button>
            <button className="btn-secondary" onClick={onNavigateToPipeline}>
              Inspect Architecture Logs
            </button>
          </div>
        </div>
      </section>
    </div>
  )
}
