# ResumeIQ

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1-green)](https://flask.palletsprojects.com)
[![Groq](https://img.shields.io/badge/Groq-LLaMA%203.3%2070B-purple)](https://groq.com)
[![React](https://img.shields.io/badge/React-Vite-61DAFB)](https://vitejs.dev)
[![Status](https://img.shields.io/badge/Status-Live-brightgreen)](https://your-demo-url.vercel.app)

AI-powered resume analysis tool. Upload a PDF resume, paste a job description, get a match score, missing keywords, and rewritten bullet points in under 30 seconds.

🔗 **Live demo:** [your-demo-url.vercel.app](https://your-demo-url.vercel.app)
📹 **Demo video:** [Loom](https://loom.com/share/your-video-id)
📐 **Technical decisions:** [docs/DECISIONS.md](docs/DECISIONS.md)

---

## The problem

ATS systems reject 75% of resumes before a human sees them — usually because of missing keywords, not missing skills. This tool gives instant, specific, actionable feedback in under 30 seconds.

---

## System architecture

```
PDF Upload (React + Vite)
│
▼
Flask Backend (Python 3.11)
│
├─► pdfplumber — text extraction + scanned PDF detection
│
└─► Groq LLaMA 3.3 70B — structured analysis
    │
    ├─ JSON mode (response_format: json_object)
    ├─ Schema validation (validate_schema)
    ├─ Retry with exponential backoff (3 attempts)
    └─ Fallback to LLaMA 3.1 8B if primary fails
    │
    └─ Outputs: match_score, missing_keywords,
               strengths, weak_sections (before/after rewrites),
               recommendation
```

---

## Features

| Feature | Description |
|---------|-------------|
| Match score | 0–100 with rationale and colour-coded ring |
| Missing keywords | Keywords from the JD absent in the resume |
| Strengths | What you have that the JD asks for |
| Bullet rewrites | Before/after cards with specific improvements |
| Batch mode | Up to 20 resumes ranked against one JD (recruiter feature) |
| Streaming | Tokens stream in real-time via SSE |
| Retry logic | 3 attempts with exponential backoff + model fallback |
| Scanned PDF detection | User-friendly error for image-based PDFs |

---

## Tech stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Frontend | React · Vite · TypeScript | Type-safe, fast HMR |
| Styling | Pure CSS with CSS variables | No framework lock-in |
| Backend | Flask 3.1 · Python 3.11 | Simple, readable AI code |
| LLM | Groq API · LLaMA 3.3 70B | 5× faster than OpenAI, generous free tier |
| Fallback LLM | LLaMA 3.1 8B | Fast + cheap backup model |
| PDF parsing | pdfplumber | Better layout handling than PyPDF2 |
| Deployment | Vercel (frontend) · Railway (backend) | Free tier, zero config |

See [docs/DECISIONS.md](docs/DECISIONS.md) for the detailed reasoning behind every choice.

---

## AI Engineering details

### Prompt design
The system prompt in `backend/prompts/analyze_resume.txt` instructs the model to:
- Return **only JSON** with a strict schema (no markdown, no preamble)
- Use a scoring rubric (85–100 = strong, 65–84 = moderate, etc.)
- Write rewrites with action verbs + quantified impact
- Extract missing keywords by comparing JD vs. resume skills

### Structured output pipeline
```python
# 1. Force JSON mode at the API level
response_format={"type": "json_object"}

# 2. Validate every required key and type
valid, err = validate_schema(data)

# 3. Regex fallback if model adds markdown fences
data = extract_json_from_text(raw)

# 4. Retry with backoff if any step fails
time.sleep(1.5 ** attempt)
```

### Eval framework
`backend/evals/run_evals.py` contains 20 annotated resume+JD pairs with expected scores.
Run `python evals/run_evals.py` to measure model accuracy.

---

## Local setup

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # add your GROQ_API_KEY
python main.py            # runs on http://localhost:5000

# Frontend (new terminal)
cd frontend
npm install
npm run dev               # runs on http://localhost:5173
```

Get a free Groq API key at [console.groq.com](https://console.groq.com).

---

## API reference

### `POST /analyze`
Single resume analysis.
```
Form data:
  resume: File (PDF)
  job_description: string
```

### `POST /analyze/stream`
Same as above, but streams tokens via Server-Sent Events.

### `POST /batch`
Multi-resume analysis for recruiters.
```
Form data:
  resumes: File[] (up to 20 PDFs)
  job_description: string
```

### `GET /health`
Returns `{"status": "ok", "model": "llama-3.3-70b-versatile"}`

---

Built by [Muneera Ibrahim](https://github.com/muneeracodes)
