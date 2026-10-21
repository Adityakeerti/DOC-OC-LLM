import React from 'react'

export default function Technology() {
  return (
    <div className="page-fade-in">
      {/* Technology Hero Section */}
      <section className="product-tile-dark tech-hero-section">
        <div className="tile-content">
          <span className="tile-tagline">Deep ML Systems Engineering</span>
          <h1 className="display-xl hero-display">Architectural Pipeline & Benchmark Audit</h1>
          <p className="tile-lead" style={{ maxWidth: 740 }}>
            DOC-OC v2 replaces brittle multi-stage cascades (Canny contour cropping, YOLO logo classifiers, Haar cascades, TableTransformers, and regex) with a unified spatial Vision-Language Model pipeline architected for edge GPU inference and low-cost deployment.
          </p>
        </div>
      </section>

      {/* Visual Flowchart representation - The 3 Pillars */}
      <section className="product-tile-dark flowchart-section">
        <div className="tile-content">
          <h2 className="display-lg">The 3-Pillar Unified Pipeline</h2>
          <p className="tile-lead" style={{ maxWidth: 640 }}>
            From raw photographic upload or vector PDF scan to certified, arithmetically validated structured JSON:
          </p>

          <div className="visual-pipeline">
            <div className="pipeline-step">
              <div className="step-number" style={{ color: '#0ea5e9' }}>01</div>
              <div className="step-title">Non-Destructive Preprocessing</div>
              <div className="step-desc">
                PyMuPDF 2× matrix rasterization for vector-crisp text. Auto-EXIF orientation correction for mobile snaps. Proportional 1200px Lanczos scaling (43% fewer visual tokens).
              </div>
              <div style={{ fontSize: 11, fontFamily: 'monospace', color: '#0ea5e9', marginTop: 8 }}>
                pipeline/preprocess.py
              </div>
            </div>

            <div className="pipeline-arrow">➔</div>

            <div className="pipeline-step">
              <div className="step-number" style={{ color: '#22c55e' }}>02</div>
              <div className="step-title">C++ GBNF Constrained Inference</div>
              <div className="step-desc">
                Gemma-4-E2B execution with token-level logit masking via GBNF grammar. Reasoning traces disabled to eliminate 1500+ token thinking lag (achieving 83 tok/s on local reference GPU testbed).
              </div>
              <div style={{ fontSize: 11, fontFamily: 'monospace', color: '#22c55e', marginTop: 8 }}>
                pipeline/extract.py
              </div>
            </div>

            <div className="pipeline-arrow">➔</div>

            <div className="pipeline-step">
              <div className="step-number" style={{ color: '#f59e0b' }}>03</div>
              <div className="step-title">Self-Healing Arithmetic Validation</div>
              <div className="step-desc">
                Strict Pydantic models with automated reconciliation: verifying Theory + Practical == Total Obtained marks, cross-checking max marks vs percentages, and disambiguating candidate vs parent names.
              </div>
              <div style={{ fontSize: 11, fontFamily: 'monospace', color: '#f59e0b', marginTop: 8 }}>
                pipeline/validate.py
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Deep Systems Engineering Innovations */}
      <section className="product-tile-dark specs-section">
        <div className="tile-content">
          <h2 className="display-lg">Systems Optimizations & Discoveries</h2>
          <p className="tile-lead" style={{ maxWidth: 680 }}>
            Key performance levers that brought average extraction latency down from 27.12s to 6.28s.
          </p>
          
          <div className="features-grid">
            {/* Spotlight Card 1: Eliminating Reasoning Lag */}
            <div className="gradient-spotlight-card">
              <div className="card-badge-dot" style={{ backgroundColor: '#22c55e' }}></div>
              <div className="card-title">Eliminating Reasoning Token Lag (4.32× Speedup)</div>
              <div className="card-desc">
                Modern reasoning VLMs default to emitting long internal thought chains (<code>reasoning_content</code>), bloating latency by generating &gt;1,500 conversational tokens before emitting JSON.
                By configuring <code>llama-server</code> with <code>--reasoning off</code> and <code>--reasoning-budget 0</code>, generation is redirected purely to structured output, reducing latency to <strong>4.2s–6.8s</strong> at 83 tokens/second.
              </div>
            </div>

            {/* Spotlight Card 2: C++ GBNF Constrained Logit Decoding */}
            <div className="gradient-spotlight-card-magenta">
              <div className="card-badge-dot" style={{ backgroundColor: '#0ea5e9' }}></div>
              <div className="card-title">C++ GBNF Logit Grammar Masking</div>
              <div className="card-desc">
                Standard autoregressive sampling often slips into markdown wrappers (<code>```json</code>), trailing commas, or leading-zero octal violations (e.g. roll numbers like <code>077</code> failing JSON.parse).
                We compile our Pydantic schema into a strict GBNF grammar. The C++ sampler masks all illegal token logits during generation, making syntax errors physically impossible.
              </div>
            </div>

            {/* Spotlight Card 3: ShortGPT Layer Redundancy */}
            <div className="gradient-spotlight-card-coral">
              <div className="card-badge-dot" style={{ backgroundColor: '#6366f1' }}></div>
              <div className="card-title">ShortGPT Layer Redundancy Profiling</div>
              <div className="card-desc">
                Using the ShortGPT block importance metric, we profiled cosine similarity across all 35 transformer blocks:
                Early blocks (0–5) are essential for spatial token grounding (Cosine Sim 0.75–0.79). Peak redundancy occurs at <strong>Blocks 14 & 15 (Cosine Sim 0.8953, Angular Dist 0.1470)</strong>. Gemma-4-E2B incorporates Per-Layer Embeddings (PLE) <code>[8960, 262144]</code>, making surgical pruning unnecessary.
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Empirical Benchmark Comparison Table */}
      <section className="product-tile-dark" style={{ borderTop: '1px solid var(--color-hairline)' }}>
        <div className="tile-content">
          <h2 className="display-lg">Multi-Board Model Comparison Matrix</h2>
          <p className="tile-lead" style={{ maxWidth: 700 }}>
            Empirical benchmark evaluated on authentic multi-board Indian educational documents on a local reference testbed (consumer laptop GPU with 6 GB VRAM) using llama.cpp with CUDA and FlashAttention-2.
          </p>

          {/* Cloud Instance Notice & YouTube Video Banner */}
          <div style={{
            marginTop: 16,
            marginBottom: 20,
            padding: '14px 18px',
            background: 'linear-gradient(90deg, rgba(239, 68, 68, 0.1) 0%, rgba(30, 41, 59, 0.7) 100%)',
            border: '1px solid rgba(239, 68, 68, 0.28)',
            borderRadius: 12,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: 14,
            width: '100%',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, flex: '1 1 380px' }}>
              <div style={{
                width: 30,
                height: 30,
                borderRadius: 8,
                background: 'rgba(239, 68, 68, 0.2)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#ef4444',
                flexShrink: 0
              }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
                </svg>
              </div>
              <div style={{ fontSize: 13, color: '#e2e8f0', lineHeight: 1.5 }}>
                <strong style={{ color: '#f87171' }}>Local Benchmark Reference:</strong> The table below records metrics measured on an offline testbed. The public web app is deployed on a free cloud instance (subject to cold-start queueing), so latency will differ. Watch our recorded benchmark execution on YouTube for verified performance.
              </div>
            </div>

            <a
              href="https://youtu.be/OsfTcbbgvao"
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                background: '#dc2626',
                color: '#ffffff',
                padding: '8px 16px',
                borderRadius: 8,
                fontSize: 12,
                fontWeight: 600,
                textDecoration: 'none',
                whiteSpace: 'nowrap',
                boxShadow: '0 2px 8px rgba(220, 38, 38, 0.35)',
              }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                <path d="M8 5v14l11-7z"/>
              </svg>
              Watch Benchmark Video ↗
            </a>
          </div>

          <div style={{ width: '100%', overflowX: 'auto', marginTop: 16 }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: 14 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--color-hairline)', color: 'var(--color-ink-muted)', fontSize: 13, textTransform: 'uppercase' }}>
                  <th style={{ padding: '12px 16px' }}>Model & Pipeline</th>
                  <th style={{ padding: '12px 16px' }}>Engine & Configuration</th>
                  <th style={{ padding: '12px 16px', textAlign: 'right' }}>Avg Latency</th>
                  <th style={{ padding: '12px 16px', textAlign: 'right' }}>Throughput</th>
                  <th style={{ padding: '12px 16px', textAlign: 'right' }}>Schema Adherence</th>
                  <th style={{ padding: '12px 16px', textAlign: 'right' }}>VRAM</th>
                  <th style={{ padding: '12px 16px', textAlign: 'center' }}>Verdict</th>
                </tr>
              </thead>
              <tbody>
                <tr style={{ borderBottom: '1px solid var(--color-hairline)', background: 'rgba(34,197,94,0.06)' }}>
                  <td style={{ padding: '14px 16px', fontWeight: 600, color: '#ffffff' }}>
                    Gemma-4-E2B (DOC-OC v2)
                  </td>
                  <td style={{ padding: '14px 16px', color: 'var(--color-ink-muted)' }}>
                    llama.cpp CUDA, 0 reasoning budget, GBNF logit mask
                  </td>
                  <td style={{ padding: '14px 16px', textAlign: 'right', fontWeight: 700, color: '#22c55e', fontFamily: 'monospace' }}>
                    6.28 s
                  </td>
                  <td style={{ padding: '14px 16px', textAlign: 'right', fontFamily: 'monospace' }}>
                    83 tok/s
                  </td>
                  <td style={{ padding: '14px 16px', textAlign: 'right', color: '#22c55e', fontWeight: 600 }}>
                    100.0%
                  </td>
                  <td style={{ padding: '14px 16px', textAlign: 'right', fontFamily: 'monospace' }}>
                    3.2 GB
                  </td>
                  <td style={{ padding: '14px 16px', textAlign: 'center' }}>
                    <span style={{ background: 'rgba(34,197,94,0.15)', color: '#22c55e', padding: '3px 8px', borderRadius: 4, fontSize: 12, fontWeight: 600 }}>
                      Active Production
                    </span>
                  </td>
                </tr>

                <tr style={{ borderBottom: '1px solid var(--color-hairline)' }}>
                  <td style={{ padding: '14px 16px', fontWeight: 500 }}>
                    Gemma-4-E2B (Baseline)
                  </td>
                  <td style={{ padding: '14px 16px', color: 'var(--color-ink-muted)' }}>
                    llama.cpp CUDA, default reasoning token budget
                  </td>
                  <td style={{ padding: '14px 16px', textAlign: 'right', fontFamily: 'monospace', color: '#f59e0b' }}>
                    27.12 s
                  </td>
                  <td style={{ padding: '14px 16px', textAlign: 'right', fontFamily: 'monospace' }}>
                    76 tok/s
                  </td>
                  <td style={{ padding: '14px 16px', textAlign: 'right' }}>
                    100.0%
                  </td>
                  <td style={{ padding: '14px 16px', textAlign: 'right', fontFamily: 'monospace' }}>
                    2.7 GB
                  </td>
                  <td style={{ padding: '14px 16px', textAlign: 'center' }}>
                    <span style={{ color: 'var(--color-ink-muted)', fontSize: 12 }}>Day 1 Baseline</span>
                  </td>
                </tr>

                <tr style={{ borderBottom: '1px solid var(--color-hairline)' }}>
                  <td style={{ padding: '14px 16px', fontWeight: 500 }}>
                    UI-TARS-7B-DPO
                  </td>
                  <td style={{ padding: '14px 16px', color: 'var(--color-ink-muted)' }}>
                    vLLM / llama.cpp standard unconstrained decoding
                  </td>
                  <td style={{ padding: '14px 16px', textAlign: 'right', fontFamily: 'monospace', color: '#ef4444' }}>
                    36.55 s
                  </td>
                  <td style={{ padding: '14px 16px', textAlign: 'right', fontFamily: 'monospace' }}>
                    38 tok/s
                  </td>
                  <td style={{ padding: '14px 16px', textAlign: 'right', color: '#ef4444' }}>
                    75.0%
                  </td>
                  <td style={{ padding: '14px 16px', textAlign: 'right', fontFamily: 'monospace' }}>
                    5.7 GB
                  </td>
                  <td style={{ padding: '14px 16px', textAlign: 'center' }}>
                    <span style={{ background: 'rgba(239,68,68,0.15)', color: '#ef4444', padding: '3px 8px', borderRadius: 4, fontSize: 12 }}>
                      Octal Slips / High VRAM
                    </span>
                  </td>
                </tr>

                <tr style={{ borderBottom: '1px solid var(--color-hairline)' }}>
                  <td style={{ padding: '14px 16px', fontWeight: 500 }}>
                    Qwen2.5-VL-3B-Instruct
                  </td>
                  <td style={{ padding: '14px 16px', color: 'var(--color-ink-muted)' }}>
                    llama.cpp GBNF grammar constraint
                  </td>
                  <td style={{ padding: '14px 16px', textAlign: 'right', fontFamily: 'monospace' }}>
                    –
                  </td>
                  <td style={{ padding: '14px 16px', textAlign: 'right', fontFamily: 'monospace' }}>
                    –
                  </td>
                  <td style={{ padding: '14px 16px', textAlign: 'right', color: '#ef4444' }}>
                    0.0%
                  </td>
                  <td style={{ padding: '14px 16px', textAlign: 'right', fontFamily: 'monospace' }}>
                    3.1 GB
                  </td>
                  <td style={{ padding: '14px 16px', textAlign: 'center' }}>
                    <span style={{ background: 'rgba(239,68,68,0.15)', color: '#ef4444', padding: '3px 8px', borderRadius: 4, fontSize: 12 }}>
                      Logit Crash on GBNF
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Latency by Board Breakdown */}
      <section className="product-tile-dark" style={{ borderTop: '1px solid var(--color-hairline)' }}>
        <div className="tile-content">
          <h2 className="display-lg">Per-Board Warm Latency Breakdown</h2>
          <p className="tile-lead" style={{ maxWidth: 680 }}>
            Audited execution duration across diverse Indian educational board marksheets on local reference testbed (offline hardware):
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16, width: '100%', marginTop: 12 }}>
            {[
              { board: "ISC 12th Certificate (icse.jpg)", time: "6.32s", width: "62%", color: "#22c55e" },
              { board: "CBSE 10th Standard (cbse.pdf)", time: "8.15s", width: "79%", color: "#0ea5e9" },
              { board: "CBSE 12th Senior Sec (12_3.jpg)", time: "7.28s", width: "71%", color: "#0ea5e9" },
              { board: "UBSE 12th Uttarakhand (uk2.pdf)", time: "6.95s", width: "68%", color: "#22c55e" },
              { board: "BSEH 12th Haryana Board", time: "5.78s", width: "56%", color: "#22c55e" },
              { board: "UPMSP 10th High School (Pink)", time: "7.32s", width: "72%", color: "#f59e0b" },
            ].map((item, i) => (
              <div key={i} style={{ background: 'var(--color-surface-1)', border: '1px solid var(--color-hairline)', borderRadius: 10, padding: '14px 16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 8 }}>
                  <span style={{ fontWeight: 500 }}>{item.board}</span>
                  <span style={{ fontFamily: 'monospace', fontWeight: 600, color: item.color }}>{item.time}</span>
                </div>
                <div style={{ height: 6, background: 'var(--color-hairline)', borderRadius: 999, overflow: 'hidden' }}>
                  <div style={{ width: item.width, height: '100%', background: item.color, borderRadius: 999 }}></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  )
}
