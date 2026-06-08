import { type AnalysisResult } from "../../lib/api";

interface Props {
  result: AnalysisResult;
  onReset: () => void;
  compact?: boolean;
}

const SCORE_CONFIG = {
  strong_match: { label: "Strong Match", color: "score-green", emoji: "🎯" },
  moderate_match: { label: "Moderate Match", color: "score-amber", emoji: "📊" },
  weak_match: { label: "Weak Match", color: "score-orange", emoji: "⚠️" },
  no_match: { label: "No Match", color: "score-red", emoji: "❌" },
};

function ScoreRing({ score }: { score: number }) {
  const radius = 52;
  const circ = 2 * Math.PI * radius;
  const fill = (score / 100) * circ;
  const color =
    score >= 75 ? "#22c55e" : score >= 50 ? "#f59e0b" : score >= 30 ? "#f97316" : "#ef4444";

  return (
    <svg width="130" height="130" viewBox="0 0 130 130">
      <circle cx="65" cy="65" r={radius} fill="none" stroke="var(--border)" strokeWidth="10" />
      <circle
        cx="65"
        cy="65"
        r={radius}
        fill="none"
        stroke={color}
        strokeWidth="10"
        strokeLinecap="round"
        strokeDasharray={`${fill} ${circ}`}
        strokeDashoffset={circ * 0.25}
        style={{ transition: "stroke-dasharray 1s ease" }}
      />
      <text x="65" y="60" textAnchor="middle" fontSize="28" fontWeight="600" fill="var(--text-primary)">{score}</text>
      <text x="65" y="78" textAnchor="middle" fontSize="11" fill="var(--text-muted)">out of 100</text>
    </svg>
  );
}

export default function ResultPanel({ result, onReset, compact = false }: Props) {
  const config = SCORE_CONFIG[result.recommendation] || SCORE_CONFIG.moderate_match;

  return (
    <div className={`result-panel ${compact ? "compact" : ""}`}>
      {!compact && (
        <div className="result-header">
          <button className="back-btn" onClick={onReset}>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M10 4L6 8l4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            New analysis
          </button>
          {result.filename && (
            <span className="result-filename">{result.filename}</span>
          )}
        </div>
      )}

      {/* Score */}
      <div className="score-section">
        <ScoreRing score={result.match_score} />
        <div className="score-meta">
          <span className={`match-badge ${config.color}`}>
            {config.emoji} {config.label}
          </span>
          <p className="score-rationale">{result.score_rationale}</p>
          {result.model_used && (
            <p className="model-tag">via {result.model_used}</p>
          )}
        </div>
      </div>

      {/* Strengths */}
      {result.strengths.length > 0 && (
        <div className="result-block">
          <h2 className="block-title">
            <span className="block-icon green-icon">✓</span>
            Strengths
          </h2>
          <ul className="strength-list">
            {result.strengths.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Missing Keywords */}
      {result.missing_keywords.length > 0 && (
        <div className="result-block">
          <h2 className="block-title">
            <span className="block-icon red-icon">!</span>
            Missing Keywords
            <span className="count-badge">{result.missing_keywords.length}</span>
          </h2>
          <div className="keyword-grid">
            {result.missing_keywords.map((kw, i) => (
              <span className="keyword-pill" key={i}>{kw}</span>
            ))}
          </div>
        </div>
      )}

      {/* Bullet Rewrites */}
      {result.weak_sections.length > 0 && (
        <div className="result-block">
          <h2 className="block-title">
            <span className="block-icon amber-icon">✎</span>
            Suggested Rewrites
          </h2>
          <div className="rewrites">
            {result.weak_sections.map((section, i) => (
              <div className="rewrite-card" key={i}>
                <div className="rewrite-before">
                  <span className="rewrite-label before-label">Before</span>
                  <p className="rewrite-text">{section.original}</p>
                </div>
                <div className="rewrite-arrow">→</div>
                <div className="rewrite-after">
                  <span className="rewrite-label after-label">After</span>
                  <p className="rewrite-text">{section.rewrite}</p>
                </div>
                <div className="rewrite-reason">
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                    <circle cx="6" cy="6" r="5" stroke="currentColor" strokeWidth="1.2" />
                    <path d="M6 4v2.5M6 8v.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
                  </svg>
                  {section.reason}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
