import React, { useState } from 'react'

export default function Developer() {
  const [activeTab, setActiveTab] = useState<'curl' | 'python' | 'ts'>('curl')
  const [copied, setCopied] = useState(false)

  const snippets = {
    curl: `curl -X POST "http://localhost:8000/process" \\
  -H "accept: application/json" \\
  -H "Content-Type: multipart/form-data" \\
  -F "file=@cbse_marksheet.jpg"`,
    python: `import requests

url = "http://localhost:8000/process"
files = {"file": open("cbse_marksheet.pdf", "rb")}

response = requests.post(url, files=files)
result = response.json()

print(f"Student: {result['data']['student_name']}")
print(f"Roll No: {result['data']['roll_number']}")
print(f"Total Marks: {result['data']['total_obtained']} / {result['data']['max_marks']}")
print(f"Inference Latency: {result['timing']['extract']}s")`,
    ts: `const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('http://localhost:8000/process', {
  method: 'POST',
  body: formData,
});

const { data, warnings, timing } = await response.json();
console.log('Candidate:', data.student_name);
console.log('Subjects:', data.subjects);
console.log(\`Processed in \${timing.extract}s via Gemma-4-E2B\`);`
  }

  const copyCode = () => {
    navigator.clipboard.writeText(snippets[activeTab])
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="page-fade-in">
      {/* Profile Card Section */}
      <section className="product-tile-dark dev-profile-section">
        <div className="tile-content">
          <div className="dev-card">
            <div className="dev-avatar" style={{ display: 'grid', placeItems: 'center', width: 80, height: 80, borderRadius: '50%', background: 'var(--color-surface-2)', margin: '0 auto 15px', color: 'var(--color-accent-blue)' }}>
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                <circle cx="12" cy="7" r="4" />
              </svg>
            </div>
            <div className="dev-name">Aditya Keerti</div>
            <div className="dev-title">Lead Architect & ML Systems Engineer</div>
            <p className="dev-bio">
              Architected DOC-OC v2 — pioneering offline edge Vision-Language Model inference with C++ GBNF grammar constrained decoding, ShortGPT layer redundancy profiling, and self-healing document validation.
            </p>
            <div className="dev-socials">
              <a href="https://adityakeerti.vercel.app" target="_blank" rel="noopener noreferrer" className="text-link">Portfolio</a>
              <span className="bullet-divider">•</span>
              <a href="https://github.com/Adityakeerti/DOC-OC-LLM" target="_blank" rel="noopener noreferrer" className="text-link">GitHub Repository</a>
              <span className="bullet-divider">•</span>
              <a href="https://x.com/adiFoundGlitch" target="_blank" rel="noopener noreferrer" className="text-link">Twitter</a>
              <span className="bullet-divider">•</span>
              <a href="mailto:adityacodes404@gmail.com" className="text-link">Email</a>
            </div>
          </div>
        </div>
      </section>

      {/* Code Snippet & Quickstart Section */}
      <section className="product-tile-dark integration-section">
        <div className="tile-content">
          <h2 className="display-lg">API Integration & Local Quickstart</h2>
          <p className="tile-lead" style={{ maxWidth: 680 }}>
            Query the DOC-OC v2 FastAPI backend directly using standard HTTP clients or launch your own 100% offline edge node.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: 24, width: '100%', alignItems: 'start' }}>
            
            {/* Left Column: API Client Code Tabs */}
            <div className="integration-container">
              <div className="tab-header">
                <button 
                  className={`tab-btn ${activeTab === 'curl' ? 'active' : ''}`}
                  onClick={() => setActiveTab('curl')}
                >
                  cURL
                </button>
                <button 
                  className={`tab-btn ${activeTab === 'python' ? 'active' : ''}`}
                  onClick={() => setActiveTab('python')}
                >
                  Python
                </button>
                <button 
                  className={`tab-btn ${activeTab === 'ts' ? 'active' : ''}`}
                  onClick={() => setActiveTab('ts')}
                >
                  TypeScript
                </button>
                <button 
                  className="tab-btn copy-btn"
                  onClick={copyCode}
                  style={{ marginLeft: 'auto', color: copied ? '#22c55e' : 'var(--color-ink-muted)' }}
                >
                  {copied ? '✓ Copied' : 'Copy Snippet'}
                </button>
              </div>

              <div className="code-block-wrapper" style={{ padding: '20px 24px', background: '#0d0d0d' }}>
                <pre style={{ margin: 0, fontFamily: 'monospace', fontSize: 13, lineHeight: 1.5, color: '#a9b1d6', overflowX: 'auto' }}>
                  {snippets[activeTab]}
                </pre>
              </div>
            </div>

            {/* Right Column: Local Inference Engine Setup */}
            <div className="gradient-spotlight-card">
              <div className="card-badge-dot" style={{ backgroundColor: '#22c55e' }}></div>
              <div className="card-title">Run 100% Offline with Zero Cloud Costs</div>
              <p className="card-desc" style={{ fontSize: 14, color: 'rgba(255, 255, 255, 0.85)', lineHeight: 1.5, marginBottom: 12 }}>
                Launch Gemma-4-E2B locally with 100% GPU offload on an NVIDIA GPU (≥6 GB VRAM) with FlashAttention-2:
              </p>
              
              <div style={{ background: 'rgba(0,0,0,0.4)', borderRadius: 8, padding: '12px 16px', fontFamily: 'monospace', fontSize: 12, color: '#38bdf8', marginBottom: 16 }}>
                <div># 1. Start local llama.cpp VLM server</div>
                <div style={{ color: '#22c55e' }}>./start_server.sh gemma</div>
                <div style={{ marginTop: 8 }}># 2. Launch FastAPI backend</div>
                <div style={{ color: '#22c55e' }}>python app.py</div>
              </div>

              <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                <a 
                  href="http://localhost:8000/docs" 
                  target="_blank" 
                  rel="noopener noreferrer" 
                  className="btn-primary" 
                  style={{ textDecoration: 'none', fontSize: 13, padding: '8px 16px' }}
                >
                  Swagger OpenAPI Docs
                </a>
                <span style={{ fontSize: 12, color: 'rgba(255, 255, 255, 0.6)' }}>
                  Interactive API Explorer on :8000
                </span>
              </div>
            </div>

          </div>
        </div>
      </section>
    </div>
  )
}
