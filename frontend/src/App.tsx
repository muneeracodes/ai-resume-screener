import React, { useState } from 'react';

type KeywordData = {
  found_keywords: string[];
  missing_keywords: string[];
};

type RewriteData = {
  section_name: string;
  current_text: string;
  suggested_rewrite: string;
};

type ReportData = {
  match_score: number;
  justification: string;
  keyword_analysis: KeywordData;
  recommended_rewrites: RewriteData[];
};

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [jd, setJd] = useState('');
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<ReportData | null>(null);
  const [error, setError] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !jd.trim()) {
      setError('Please provide both a PDF resume and a job description.');
      return;
    }

    setError('');
    setLoading(true);
    setReport(null);

    const formData = new FormData();
    formData.append('resume', file);
    formData.append('job_description', jd);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/screen', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to screen resume.');
      }

      const data: ReportData = await response.json();
      setReport(data);
    } catch (err: any) {
      setError(err.message || 'An error occurred during screening.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#0f172a', color: '#f8fafc', fontFamily: 'sans-serif', padding: '2rem' }}>
      <header style={{ textAlign: 'center', marginBottom: '3rem' }}>
        <h1 style={{ fontSize: '2.5rem', fontWeight: 'bold', color: '#38bdf8', margin: '0 0 0.5rem 0' }}>
          Enterprise AI Resume Screener
        </h1>
        <p style={{ color: '#94a3b8', margin: 0 }}>
          Deep Semantic Matching & Keyword Gap Engine powered by LLaMA 3.3 & Groq
        </p>
      </header>

      <main style={{ maxWidth: '1200px', margin: '0 auto', display: 'grid', gridTemplateColumns: report ? '1fr 1fr' : '1fr', gap: '2rem' }}>
        
        {/* INPUT PANEL */}
        <section style={{ backgroundColor: '#1e293b', padding: '2rem', borderRadius: '12px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.5)' }}>
          <h2 style={{ fontSize: '1.5rem', marginBottom: '1.5rem', borderBottom: '1px solid #334155', paddingBottom: '0.5rem' }}>Screening Parameters</h2>
          <form onSubmit={handleSubmit}>
            
            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600' }}>1. Upload Resume (PDF Only)</label>
              <input 
                type="file" 
                accept=".pdf" 
                onChange={handleFileChange}
                style={{ width: '100%', padding: '0.75rem', backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: '6px', color: '#f8fafc' }}
              />
            </div>

            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600' }}>2. Job Description</label>
              <textarea 
                rows={10}
                value={jd}
                onChange={(e) => setJd(e.target.value)}
                placeholder="Paste the full job target description requirements here..."
                style={{ width: '100%', padding: '0.75rem', backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: '6px', color: '#f8fafc', resize: 'vertical' }}
              />
            </div>

            {error && <div style={{ color: '#ef4444', backgroundColor: '#451a03', padding: '0.75rem', borderRadius: '6px', marginBottom: '1rem' }}>{error}</div>}

            <button 
              type="submit" 
              disabled={loading}
              style={{ width: '100%', padding: '1rem', backgroundColor: loading ? '#475569' : '#0284c7', color: '#fff', border: 'none', borderRadius: '6px', fontWeight: 'bold', cursor: loading ? 'not-allowed' : 'pointer', fontSize: '1rem', transition: 'background-color 0.2s' }}
            >
              {loading ? 'Analyzing Semantics with LLaMA 3.3...' : 'Run Intelligence Screening Pipeline'}
            </button>
          </form>
        </section>

        {/* ANALYSIS RESULTS PANEL */}
        {report && (
          <section style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            
            {/* MATCH SCORE BLOCK */}
            <div style={{ backgroundColor: '#1e293b', padding: '2rem', borderRadius: '12px', textAlign: 'center', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.5)' }}>
              <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.25rem', color: '#94a3b8' }}>Semantic Compatibility Match</h3>
              <div style={{ fontSize: '4rem', fontWeight: '900', color: report.match_score >= 80 ? '#22c55e' : report.match_score >= 50 ? '#eab308' : '#ef4444' }}>
                {report.match_score}%
              </div>
              <p style={{ marginTop: '1rem', color: '#cbd5e1', fontStyle: 'italic', lineHeight: '1.5' }}>"{report.justification}"</p>
            </div>

            {/* KEYWORDS BLOCK */}
            <div style={{ backgroundColor: '#1e293b', padding: '2rem', borderRadius: '12px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.5)' }}>
              <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.25rem', color: '#38bdf8', borderBottom: '1px solid #334155', paddingBottom: '0.5rem' }}>Keyword Mapping & Skills Gap</h3>
              
              <div style={{ marginBottom: '1.5rem' }}>
                <h4 style={{ color: '#22c55e', margin: '0 0 0.5rem 0' }}>Aligned Strengths ({report.keyword_analysis.found_keywords.length})</h4>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                  {report.keyword_analysis.found_keywords.map((kw, i) => (
                    <span key={i} style={{ backgroundColor: '#14532d', color: '#4ade80', padding: '0.25rem 0.75rem', borderRadius: '9999px', fontSize: '0.85rem' }}>{kw}</span>
                  ))}
                </div>
              </div>

              <div>
                <h4 style={{ color: '#ef4444', margin: '0 0 0.5rem 0' }}>Target Gaps Detected ({report.keyword_analysis.missing_keywords.length})</h4>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                  {report.keyword_analysis.missing_keywords.map((kw, i) => (
                    <span key={i} style={{ backgroundColor: '#7f1d1d', color: '#fca5a5', padding: '0.25rem 0.75rem', borderRadius: '9999px', fontSize: '0.85rem' }}>{kw}</span>
                  ))}
                </div>
              </div>
            </div>

            {/* REWRITES BLOCK */}
            <div style={{ backgroundColor: '#1e293b', padding: '2rem', borderRadius: '12px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.5)' }}>
              <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.25rem', color: '#a855f7', borderBottom: '1px solid #334155', paddingBottom: '0.5rem' }}>AI-Generated Profile Optimization</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {report.recommended_rewrites.map((rw, i) => (
                  <div key={i} style={{ borderLeft: '4px solid #a855f7', paddingLeft: '1rem', marginBottom: '0.5rem' }}>
                    <h4 style={{ margin: '0 0 0.25rem 0', color: '#e2e8f0', fontSize: '1rem' }}>Section: {rw.section_name}</h4>
                    <p style={{ color: '#94a3b8', fontSize: '0.9rem', textDecoration: 'line-through', margin: '0 0 0.25rem 0' }}>{rw.current_text}</p>
                    <p style={{ color: '#e9d5ff', fontSize: '0.95rem', fontWeight: '500', margin: 0 }}>✨ {rw.suggested_rewrite}</p>
                  </div>
                ))}
              </div>
            </div>

          </section>
        )}
      </main>
    </div>
  );
}