import { useState, useRef } from "react";
import { analyzeResume, type AnalysisResult } from "../../lib/api";
import ResultPanel from "./ResultPanel";

type Status = "idle" | "loading" | "done" | "error";

export default function SingleAnalyzer() {
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [jobDesc, setJobDesc] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [errorMsg, setErrorMsg] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = (file: File) => {
    if (!file.name.endsWith(".pdf")) {
      setErrorMsg("Only PDF files are supported.");
      return;
    }
    setResumeFile(file);
    setErrorMsg("");
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  const handleSubmit = async () => {
    if (!resumeFile || !jobDesc.trim()) return;

    setStatus("loading");
    setResult(null);
    setErrorMsg("");

    try {
      const data = await analyzeResume(resumeFile, jobDesc);
      if (data.error) {
        setErrorMsg("Analysis failed. Please try again.");
        setStatus("error");
      } else {
        setResult(data);
        setStatus("done");
      }
    } catch (e: any) {
      if (e.message?.includes("scanned")) {
        setErrorMsg(
          "This PDF appears to be a scanned image. Please upload a text-based PDF."
        );
      } else {
        setErrorMsg(e.message || "Something went wrong.");
      }
      setStatus("error");
    }
  };

  const reset = () => {
    setStatus("idle");
    setResult(null);
    setResumeFile(null);
    setJobDesc("");
    setErrorMsg("");
  };

  if (status === "done" && result) {
    return <ResultPanel result={result} onReset={reset} />;
  }

  return (
    <div className="analyzer-layout">
      <div className="analyzer-hero">
        <p className="hero-eyebrow">AI-powered</p>
        <h1 className="hero-title">Resume Scanner</h1>
        <p className="hero-sub">
          Know exactly why your resume isn't getting callbacks — in 30 seconds.
        </p>
      </div>

      <div className="form-card">
        {/* Drop Zone */}
        <div
          className={`drop-zone ${isDragging ? "dragging" : ""} ${resumeFile ? "has-file" : ""}`}
          onClick={() => fileInputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            style={{ display: "none" }}
            onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
          />
          {resumeFile ? (
            <div className="file-preview">
              <div className="file-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                  <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
                  <path d="M14 2v6h6" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
                  <path d="M9 13h6M9 17h4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
              </div>
              <div>
                <p className="file-name">{resumeFile.name}</p>
                <p className="file-size">{(resumeFile.size / 1024).toFixed(0)} KB · PDF</p>
              </div>
              <button className="file-remove" onClick={(e) => { e.stopPropagation(); setResumeFile(null); }}>
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                  <path d="M2 2l10 10M12 2L2 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
              </button>
            </div>
          ) : (
            <div className="drop-placeholder">
              <div className="drop-icon">
                <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
                  <path d="M14 18V6M14 6l-4 4M14 6l4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                  <path d="M4 20v2a2 2 0 002 2h16a2 2 0 002-2v-2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
              </div>
              <p className="drop-text">Drop your resume here</p>
              <p className="drop-sub">or click to browse · PDF only</p>
            </div>
          )}
        </div>

        {/* Job Description */}
        <div className="field">
          <label className="field-label">Job Description</label>
          <textarea
            className="jd-textarea"
            placeholder="Paste the full job description here — the more detail, the better the analysis..."
            value={jobDesc}
            onChange={(e) => setJobDesc(e.target.value)}
            rows={8}
          />
          <p className="field-hint">{jobDesc.length} characters · aim for 200+</p>
        </div>

        {errorMsg && (
          <div className="error-banner">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.5" />
              <path d="M8 5v3M8 11v.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
            {errorMsg}
          </div>
        )}

        <button
          className="analyze-btn"
          disabled={!resumeFile || jobDesc.length < 50 || status === "loading"}
          onClick={handleSubmit}
        >
          {status === "loading" ? (
            <>
              <span className="spinner" />
              Analyzing...
            </>
          ) : (
            <>
              Analyze Resume
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </>
          )}
        </button>

        {status === "loading" && (
          <div className="loading-steps">
            <div className="step active">Extracting PDF text</div>
            <div className="step-sep">→</div>
            <div className="step active">LLaMA 3.3 analyzing</div>
            <div className="step-sep">→</div>
            <div className="step">Generating rewrites</div>
          </div>
        )}
      </div>

      <div className="features-row">
        {[
          { icon: "⚡", label: "Under 30 seconds" },
          { icon: "🎯", label: "Keyword gap analysis" },
          { icon: "✍️", label: "AI bullet rewrites" },
          { icon: "📊", label: "0–100 match score" },
        ].map((f) => (
          <div className="feature-chip" key={f.label}>
            <span>{f.icon}</span>
            <span>{f.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
