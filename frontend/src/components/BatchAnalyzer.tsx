import { useState, useRef } from "react";
import { batchAnalyze, type BatchResult, type AnalysisResult } from "../../lib/api";
import ResultPanel from "./ResultPanel";

export default function BatchAnalyzer() {
  const [files, setFiles] = useState<File[]>([]);
  const [jobDesc, setJobDesc] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "done" | "error">("idle");
  const [batchResult, setBatchResult] = useState<BatchResult | null>(null);
  const [selectedResult, setSelectedResult] = useState<AnalysisResult | null>(null);
  const [errorMsg, setErrorMsg] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFiles = (newFiles: FileList | null) => {
    if (!newFiles) return;
    const pdfs = Array.from(newFiles).filter((f) => f.name.endsWith(".pdf"));
    const combined = [...files, ...pdfs].slice(0, 20);
    setFiles(combined);
  };

  const removeFile = (index: number) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  const handleSubmit = async () => {
    if (files.length === 0 || !jobDesc.trim()) return;
    setStatus("loading");
    setErrorMsg("");
    try {
      const data = await batchAnalyze(files, jobDesc);
      setBatchResult(data);
      setStatus("done");
    } catch (e: any) {
      setErrorMsg(e.message || "Batch analysis failed");
      setStatus("error");
    }
  };

  const reset = () => {
    setStatus("idle");
    setBatchResult(null);
    setFiles([]);
    setJobDesc("");
    setSelectedResult(null);
  };

  const scoreColor = (score: number) =>
    score >= 75 ? "rank-green" : score >= 50 ? "rank-amber" : score >= 30 ? "rank-orange" : "rank-red";

  if (selectedResult) {
    return (
      <div className="analyzer-layout">
        <button className="back-btn" style={{ marginBottom: "1.5rem" }} onClick={() => setSelectedResult(null)}>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M10 4L6 8l4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          Back to rankings
        </button>
        <ResultPanel result={selectedResult} onReset={() => setSelectedResult(null)} />
      </div>
    );
  }

  if (status === "done" && batchResult) {
    return (
      <div className="analyzer-layout">
        <div className="batch-summary">
          <div className="batch-stat">
            <span className="stat-num">{batchResult.total}</span>
            <span className="stat-label">uploaded</span>
          </div>
          <div className="batch-stat">
            <span className="stat-num green-num">{batchResult.successful}</span>
            <span className="stat-label">analyzed</span>
          </div>
          <div className="batch-stat">
            <span className="stat-num red-num">{batchResult.failed}</span>
            <span className="stat-label">failed</span>
          </div>
          <button className="back-btn" style={{ marginLeft: "auto" }} onClick={reset}>
            New batch
          </button>
        </div>

        <p className="batch-jd-preview">
          JD: "{batchResult.job_description_preview}..."
        </p>

        <div className="rankings-table">
          <div className="rankings-header">
            <span>Rank</span>
            <span>Candidate</span>
            <span>Score</span>
            <span>Match</span>
            <span>Missing keywords</span>
            <span></span>
          </div>
          {batchResult.results.map((r) => (
            <div key={r.rank} className="rankings-row" onClick={() => setSelectedResult(r)}>
              <span className="rank-num">#{r.rank}</span>
              <span className="candidate-name">{r.filename?.replace(".pdf", "")}</span>
              <span className={`score-pill ${scoreColor(r.match_score)}`}>{r.match_score}</span>
              <span className={`rec-label ${r.recommendation}`}>
                {r.recommendation?.replace("_", " ")}
              </span>
              <span className="missing-preview">
                {r.missing_keywords?.slice(0, 3).join(", ")}
                {r.missing_keywords?.length > 3 && ` +${r.missing_keywords.length - 3}`}
              </span>
              <span className="view-link">
                View →
              </span>
            </div>
          ))}
        </div>

        {batchResult.errors.length > 0 && (
          <div className="batch-errors">
            <p className="errors-title">Failed ({batchResult.errors.length})</p>
            {batchResult.errors.map((e, i) => (
              <div key={i} className="error-row">{e.filename}: {e.error}</div>
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="analyzer-layout">
      <div className="analyzer-hero">
        <p className="hero-eyebrow">Recruiter mode</p>
        <h1 className="hero-title">Batch Screener</h1>
        <p className="hero-sub">
          Upload up to 20 resumes at once. Get a ranked shortlist in seconds.
        </p>
      </div>

      <div className="form-card">
        {/* Multi-file drop zone */}
        <div
          className="drop-zone multi"
          onClick={() => fileInputRef.current?.click()}
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => { e.preventDefault(); handleFiles(e.dataTransfer.files); }}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            multiple
            style={{ display: "none" }}
            onChange={(e) => handleFiles(e.target.files)}
          />
          <div className="drop-placeholder">
            <div className="drop-icon">
              <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
                <path d="M14 18V6M14 6l-4 4M14 6l4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M4 20v2a2 2 0 002 2h16a2 2 0 002-2v-2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
              </svg>
            </div>
            <p className="drop-text">Drop multiple PDFs here</p>
            <p className="drop-sub">{files.length}/20 resumes selected · click to add more</p>
          </div>
        </div>

        {/* File list */}
        {files.length > 0 && (
          <div className="file-list">
            {files.map((f, i) => (
              <div className="file-list-item" key={i}>
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                  <path d="M8 1H3a1 1 0 00-1 1v10a1 1 0 001 1h8a1 1 0 001-1V6L8 1z" stroke="currentColor" strokeWidth="1.2" />
                </svg>
                <span className="file-list-name">{f.name}</span>
                <span className="file-list-size">{(f.size / 1024).toFixed(0)}KB</span>
                <button className="file-remove-sm" onClick={() => removeFile(i)}>✕</button>
              </div>
            ))}
          </div>
        )}

        <div className="field">
          <label className="field-label">Job Description (same for all resumes)</label>
          <textarea
            className="jd-textarea"
            placeholder="Paste the job description here..."
            value={jobDesc}
            onChange={(e) => setJobDesc(e.target.value)}
            rows={6}
          />
        </div>

        {errorMsg && <div className="error-banner">{errorMsg}</div>}

        <button
          className="analyze-btn"
          disabled={files.length === 0 || jobDesc.length < 50 || status === "loading"}
          onClick={handleSubmit}
        >
          {status === "loading" ? (
            <><span className="spinner" /> Analyzing {files.length} resumes...</>
          ) : (
            <>Screen {files.length || ""} Resumes →</>
          )}
        </button>
      </div>
    </div>
  );
}
