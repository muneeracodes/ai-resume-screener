import { useState } from "react";
import SingleAnalyzer from "./components/SingleAnalyzer";
import BatchAnalyzer from "./components/BatchAnalyzer";
// @ts-ignore: side-effect CSS import without type declarations
import "./index.css";

type Mode = "single" | "batch";

export default function App() {
  const [mode, setMode] = useState<Mode>("single");

  return (
    <div className="app-shell">
      <header className="top-bar">
        <div className="logo">
          <div className="logo-mark">
            <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
              <rect x="1" y="1" width="9" height="9" rx="2" fill="currentColor" opacity="0.9"/>
              <rect x="12" y="1" width="9" height="9" rx="2" fill="currentColor" opacity="0.5"/>
              <rect x="1" y="12" width="9" height="9" rx="2" fill="currentColor" opacity="0.5"/>
              <rect x="12" y="12" width="9" height="9" rx="2" fill="currentColor" opacity="0.15"/>
            </svg>
          </div>
          <span className="logo-text">ResumeIQ</span>
        </div>

        <nav className="mode-nav">
          <button
            className={`mode-btn ${mode === "single" ? "active" : ""}`}
            onClick={() => setMode("single")}
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <circle cx="7" cy="5" r="3" stroke="currentColor" strokeWidth="1.5"/>
              <path d="M1 13c0-3.314 2.686-5 6-5s6 1.686 6 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
            Single Resume
          </button>
          <button
            className={`mode-btn ${mode === "batch" ? "active" : ""}`}
            onClick={() => setMode("batch")}
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M1 4h12M1 8h12M1 12h8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
            Batch Screener
          </button>
        </nav>

        <a
          href="https://github.com/muneeracodes/ai-resume-screener"
          target="_blank"
          rel="noreferrer"
          className="github-link"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
            <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
          </svg>
          GitHub
        </a>
      </header>

      <main className="main-content">
        {mode === "single" ? <SingleAnalyzer /> : <BatchAnalyzer />}
      </main>
    </div>
  );
}
