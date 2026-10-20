import React, { useState, useEffect } from 'react'
import Home from './Home'
import Workspace, { ExtractionResult } from './Workspace'
import Technology from './Technology'
import Developer from './Developer'

const API_BASE =
  window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? `http://${window.location.hostname}:8000`
    : (import.meta as any).env?.VITE_API_BASE || window.location.origin;

export type PipelineStep = {
  step: string
  status: 'idle' | 'running' | 'done' | 'error'
  label: string
  detail?: string
}

const INITIAL_STEPS: PipelineStep[] = [
  { step: 'preprocess', status: 'idle', label: '1. High-Fidelity Vector Preprocessing', detail: 'PyMuPDF 2.5× rasterization & Lanczos scaling' },
  { step: 'gpu_offload', status: 'idle', label: '2. Gemma-4-E2B Context Allocation', detail: 'Local GPU offload via llama.cpp CUDA (3.2 GB footprint)' },
  { step: 'reasoning_opt', status: 'idle', label: '3. Direct Token Generation', detail: 'Bypassing conversational thinking tokens for lower latency' },
  { step: 'gbnf_grammar', status: 'idle', label: '4. C++ GBNF Logit Grammar Masking', detail: 'Logit-level sampling enforcing RFC 8259 syntax' },
  { step: 'spatial_ground', status: 'idle', label: '5. Multi-Board Spatial Layout Grounding', detail: 'Spatial disambiguation of candidate and guardian fields' },
  { step: 'self_healing', status: 'idle', label: '6. Self-Healing Arithmetic Parity', detail: 'Automated parity reconciliation of Theory and Practical marks' },
]

export default function App() {
  const [currentPage, setCurrentPage] = useState<'overview' | 'workspace' | 'pipeline' | 'developer'>('overview')
  const [uploadCount, setUploadCount] = useState<number>(0)
  const [file, setFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [isPdf, setIsPdf] = useState<boolean>(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<ExtractionResult | null>(null)
  const [editable, setEditable] = useState(false)
  const [localSubjects, setLocalSubjects] = useState<any[]>([])
  const [localInfo, setLocalInfo] = useState<any>({})
  const [pipelineSteps, setPipelineSteps] = useState<PipelineStep[]>(INITIAL_STEPS)
  const [elapsedTime, setElapsedTime] = useState<number>(0)

  // Timer for loading feedback
  useEffect(() => {
    let interval: any = null
    if (loading) {
      const startTime = Date.now()
      interval = setInterval(() => {
        setElapsedTime(Date.now() - startTime)
      }, 100)
    } else {
      setElapsedTime(0)
    }
    return () => clearInterval(interval)
  }, [loading])

  const processFile = async (selectedFile: File) => {
    setFile(selectedFile)
    const isPdfFile = selectedFile.type === 'application/pdf' || selectedFile.name.toLowerCase().endsWith('.pdf')
    setIsPdf(isPdfFile)
    
    // Create immediate local object URL for preview
    const localUrl = URL.createObjectURL(selectedFile)
    setPreviewUrl(localUrl)

    setLoading(true)
    setError(null)
    setResult(null)
    setEditable(false)

    // Reset steps to initial
    setPipelineSteps(INITIAL_STEPS.map(s => ({ ...s, status: 'idle' })))

    // Progression timer for realistic visual feedback of the 6 v2 stages
    const stepIntervals = [
      setTimeout(() => setPipelineSteps(prev => prev.map((s, idx) => idx === 0 ? { ...s, status: 'running' } : s)), 50),
      setTimeout(() => setPipelineSteps(prev => prev.map((s, idx) => idx === 0 ? { ...s, status: 'done' } : idx === 1 ? { ...s, status: 'running' } : s)), 600),
      setTimeout(() => setPipelineSteps(prev => prev.map((s, idx) => idx <= 1 ? { ...s, status: 'done' } : idx === 2 ? { ...s, status: 'running' } : s)), 1500),
      setTimeout(() => setPipelineSteps(prev => prev.map((s, idx) => idx <= 2 ? { ...s, status: 'done' } : idx === 3 ? { ...s, status: 'running' } : s)), 2800),
      setTimeout(() => setPipelineSteps(prev => prev.map((s, idx) => idx <= 3 ? { ...s, status: 'done' } : idx === 4 ? { ...s, status: 'running' } : s)), 4200),
      setTimeout(() => setPipelineSteps(prev => prev.map((s, idx) => idx <= 4 ? { ...s, status: 'done' } : idx === 5 ? { ...s, status: 'running' } : s)), 5600),
    ]

    try {
      let resJson: ExtractionResult

      // 1. If running on local server with FastAPI backend, use standard POST /process
      if (
        window.location.hostname === 'localhost' ||
        window.location.hostname === '127.0.0.1' ||
        (import.meta as any).env?.VITE_USE_LOCAL_API === 'true'
      ) {
        const form = new FormData()
        form.append('file', selectedFile)

        const response = await fetch(`${API_BASE}/process`, {
          method: 'POST',
          body: form,
        })

        if (!response.ok) {
          const errJson = await response.json().catch(() => ({}))
          throw new Error(errJson.detail || `Server responded with ${response.status}: ${response.statusText}`)
        }

        resJson = await response.json()
      } else {
        // 2. When deployed (e.g. Vercel), connect directly to the Hugging Face ZeroGPU Space!
        const { Client } = await import('@gradio/client')
        const spaceName = (import.meta as any).env?.VITE_HF_SPACE || 'adityacodes404/doc-oc-ai'
        const hfToken = (import.meta as any).env?.VITE_HF_TOKEN
        const client = await Client.connect(spaceName, hfToken ? { token: hfToken } : {})
        const result: any = await client.predict('/process', {
          file_input: selectedFile,
        })

        const rawData = Array.isArray(result?.data) ? result.data[0] : result?.data
        if (rawData?.status === 'error') {
          throw new Error(rawData.error || 'Extraction failed on Hugging Face ZeroGPU engine.')
        }

        resJson = {
          data: rawData?.data || rawData || {},
          warnings: rawData?.warnings || [],
          timing: rawData?.timing || {},
        }
      }

      // If backend returned high-res rasterized preview (especially for PDFs or auto-rotated photos), use it!
      if (resJson.image_preview) {
        setPreviewUrl(resJson.image_preview)
      }

      // Mark all steps done
      setPipelineSteps(prev => prev.map(s => ({ ...s, status: 'done' })))

      const dataObj: any = resJson.data || {}
      const studentInfo = dataObj.student_info || {}
      const resultInfo = dataObj.result || {}

      const normalizedInfo = {
        student_name: studentInfo.name || dataObj.student_name || '',
        roll_number: studentInfo.roll_no || dataObj.roll_number || '',
        father_name: studentInfo.father_name || dataObj.father_name || '',
        mother_name: studentInfo.mother_name || dataObj.mother_name || '',
        institution_name: studentInfo.school_name || dataObj.institution_name || '',
        board_name: dataObj.board || dataObj.board_name || '',
        examination_year: dataObj.examination || dataObj.examination_year || '',
        total_obtained: resultInfo.total_obtained ?? dataObj.total_obtained ?? '',
        max_marks: resultInfo.maximum_marks ?? dataObj.max_marks ?? '',
        percentage: resultInfo.percentage ?? dataObj.percentage ?? '',
        result: resultInfo.status ?? dataObj.result ?? 'PASS',
      }

      const rawSubjects = dataObj.subjects || []
      const normalizedSubjects = rawSubjects.map((s: any) => ({
        name: s.name,
        marks_theory: s.marks_theory ?? s.theory ?? '',
        marks_practical: s.marks_practical ?? s.practical ?? '',
        total_obtained: s.total_obtained ?? s.total ?? '',
        max_marks: s.max_marks ?? 100,
        grade: s.grade || '',
      }))

      setResult(resJson)
      setLocalInfo(normalizedInfo)
      setLocalSubjects(normalizedSubjects)
      setUploadCount(prev => prev + 1)
    } catch (err: any) {
      setPipelineSteps(prev => prev.map(s => s.status === 'running' ? { ...s, status: 'error' } : s))
      setError(err?.message || 'Failed to connect to DOC-OC v2 backend. Is llama-server and FastAPI running?')
    } finally {
      stepIntervals.forEach(clearTimeout)
      setLoading(false)
    }
  }

  // Preloaded sample loader
  const runSample = async (filename: string, label: string) => {
    setLoading(true)
    setError(null)
    setResult(null)
    const sampleUrl =
      window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? `${API_BASE}/dataset/${filename}`
        : `/dataset/${filename}`
    setPreviewUrl(sampleUrl)
    setIsPdf(filename.toLowerCase().endsWith('.pdf'))
    try {
      const resp = await fetch(sampleUrl)
      if (!resp.ok) {
        throw new Error(`Sample file ${filename} not found in /dataset directory.`)
      }
      const blob = await resp.blob()
      const sampleFile = new File([blob], filename, { type: blob.type || 'image/jpeg' })
      await processFile(sampleFile)
    } catch (err: any) {
      setError(err.message || 'Error fetching sample.')
      setLoading(false)
    }
  }

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault()
  }

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault()
    if (loading) return
    const droppedFiles = e.dataTransfer.files
    if (droppedFiles && droppedFiles.length > 0) {
      processFile(droppedFiles[0])
    }
  }

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (loading) return
    const selected = e.target.files
    if (selected && selected.length > 0) {
      processFile(selected[0])
    }
  }

  const handleCellChange = (idx: number, key: string, val: string) => {
    const updated = [...localSubjects]
    updated[idx] = { ...updated[idx], [key]: val }
    setLocalSubjects(updated)
  }

  const handleInfoChange = (key: string, val: string) => {
    setLocalInfo((prev: any) => ({ ...prev, [key]: val }))
  }

  return (
    <div className="landing-container">
      {/* Global Pinned Navbar */}
      <nav className="global-nav">
        <div className="nav-title" onClick={() => setCurrentPage('overview')} style={{ cursor: 'pointer' }}>
          <svg className="nav-logo-svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: 8, color: 'var(--color-accent-blue)', display: 'inline-block', verticalAlign: 'middle' }}>
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
          </svg>
          <span style={{ fontWeight: 600, letterSpacing: -0.5 }}>DOC-OC</span>
          <span className="nav-badge" style={{ color: '#22c55e', borderColor: 'rgba(34,197,94,0.3)', background: 'rgba(34,197,94,0.1)' }}>
            v2.0
          </span>
        </div>

        <div className="nav-links">
          <button onClick={() => setCurrentPage('overview')} className={`nav-tab-btn ${currentPage === 'overview' ? 'active' : ''}`}>
            Overview
          </button>
          <button onClick={() => setCurrentPage('workspace')} className={`nav-tab-btn ${currentPage === 'workspace' ? 'active' : ''}`}>
            Workspace
          </button>
          <button onClick={() => setCurrentPage('pipeline')} className={`nav-tab-btn ${currentPage === 'pipeline' ? 'active' : ''}`}>
            Architecture & Benchmarks
          </button>
          <button onClick={() => setCurrentPage('developer')} className={`nav-tab-btn ${currentPage === 'developer' ? 'active' : ''}`}>
            API & Docs
          </button>
        </div>

        <div>
          {currentPage !== 'workspace' ? (
            <button className="btn-primary" onClick={() => setCurrentPage('workspace')}>
              Launch Workspace
            </button>
          ) : (
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <span style={{ fontSize: 11, color: '#22c55e', background: 'rgba(34,197,94,0.1)', padding: '4px 8px', borderRadius: 4, fontWeight: 600 }}>
                RTX 4050 CUDA
              </span>
            </div>
          )}
        </div>
      </nav>

      {/* Main Content Router */}
      <main className="main-content">
        {currentPage === 'overview' && (
          <Home 
            onNavigateToWorkspace={() => setCurrentPage('workspace')}
            onNavigateToPipeline={() => setCurrentPage('pipeline')}
          />
        )}

        {currentPage === 'workspace' && (
          <Workspace
            uploadCount={uploadCount}
            file={file}
            previewUrl={previewUrl}
            isPdf={isPdf}
            loading={loading}
            error={error}
            result={result}
            detectedBoard={localInfo.board_name || 'AUTHENTICATED BOARD'}
            editable={editable}
            setEditable={setEditable}
            localSubjects={localSubjects}
            localInfo={localInfo}
            processFile={processFile}
            runSample={runSample}
            onDragOver={onDragOver}
            onDrop={onDrop}
            onFileChange={onFileChange}
            handleCellChange={handleCellChange}
            handleInfoChange={handleInfoChange}
            pipelineSteps={pipelineSteps}
            elapsedTime={elapsedTime}
          />
        )}

        {currentPage === 'pipeline' && (
          <Technology />
        )}

        {currentPage === 'developer' && (
          <Developer />
        )}
      </main>

      {/* Global Footer */}
      <footer className="global-footer">
        <div className="footer-content">
          <p>© {new Date().getFullYear()} DOC-OC v2 — Universal Indian Marksheet & Academic Credential Extraction Engine.</p>
          <p style={{ fontSize: 12, color: 'var(--color-ink-muted)' }}>
            Offline Edge VLM Architecture • Deterministic GBNF Parsing • Self-Healing Arithmetic • Apache-2.0 License
          </p>
          <div className="footer-links">
            <a href="https://adityakeerti.vercel.app" target="_blank" rel="noopener noreferrer" className="text-link">Developer Portfolio</a>
            <span className="bullet-divider">•</span>
            <a href="https://github.com/Adityakeerti/DOC-OC-LLM" target="_blank" rel="noopener noreferrer" className="text-link">GitHub Source</a>
            <span className="bullet-divider">•</span>
            <a href="mailto:adityacodes404@gmail.com" className="text-link">Contact Aditya Keerti</a>
          </div>
        </div>
      </footer>
    </div>
  )
}
