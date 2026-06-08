# Complete AI Resume Screener — Build Guide
### From scaffold to portfolio-ready, step by step

---

## Phase 1 — Ship the Working MVP (Days 1–2)

Your first goal is a working product, not a perfect one.
A buggy live demo beats a perfect scaffold every time.

### Step 1.1 — Get your Groq API key
1. Go to https://console.groq.com
2. Sign up (free)
3. Click "API Keys" → "Create API Key"
4. Copy the key — you get 14,400 requests/day free

### Step 1.2 — Set up the backend
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# open .env and paste your GROQ_API_KEY
python main.py
# → Running on http://localhost:5000
```

Test it:
```bash
curl -X GET http://localhost:5000/health
# should return: {"status": "ok", "model": "llama-3.3-70b-versatile"}
```

### Step 1.3 — Set up the frontend
```bash
cd frontend
npm install
# create .env.local with:
echo "VITE_API_URL=http://localhost:5000" > .env.local
npm run dev
# → Running on http://localhost:5173
```

### Step 1.4 — Test the full flow
1. Open http://localhost:5173
2. Upload a PDF resume
3. Paste a job description (200+ characters)
4. Click Analyze Resume
5. You should see results in ~15 seconds

**If it works: commit everything immediately.**
```bash
git add .
git commit -m "feat: working MVP - PDF upload, LLM analysis, results UI"
git push
```

---

## Phase 2 — Deploy (Day 2)

### Step 2.1 — Deploy backend to Railway
1. Go to https://railway.app → New Project → Deploy from GitHub
2. Select your repo → select the `backend/` folder
3. Add environment variable: `GROQ_API_KEY = your_key`
4. Railway auto-detects Python and runs `gunicorn main:app`
5. Copy your Railway URL (e.g., `https://ai-resume-screener-production.up.railway.app`)

### Step 2.2 — Deploy frontend to Vercel
1. Go to https://vercel.com → New Project → Import your GitHub repo
2. Set Root Directory to `frontend`
3. Add environment variable: `VITE_API_URL = https://your-railway-url.up.railway.app`
4. Deploy
5. Copy your Vercel URL

### Step 2.3 — Update CORS in backend
In `backend/main.py`, update the CORS origin to include your Vercel URL.
The `.env` `FRONTEND_URL` variable handles this automatically.

### Step 2.4 — Test the live deployment
Open your Vercel URL, run a full analysis. If it works — you have a live demo.

---

## Phase 3 — Record the Demo (Day 3)

### Step 3.1 — Get Loom
1. Go to https://loom.com → sign up free
2. Install the Chrome extension or desktop app

### Step 3.2 — Prepare before recording
- Have 2 test resumes ready (one good match, one weak match)
- Have 2 job descriptions ready (copy from LinkedIn)
- Clear your browser tabs
- Run a test recording first — check your mic

### Step 3.3 — Script (keep it under 2 minutes)
```
0:00 — "Hi, I'm Muneera. This is ResumeIQ, an AI resume screener
        I built using Groq's LLaMA 3.3 70B."

0:10 — Upload the strong-match resume
        "I'll upload this senior engineer resume..."

0:20 — Paste the job description
        "...and paste this Python backend role from LinkedIn."

0:30 — Click Analyze
        "The backend sends the text to LLaMA 3.3 via Groq's API,
        which returns structured JSON in about 10 seconds."

0:45 — Results appear
        Walk through: score ring, match badge, missing keywords,
        before/after rewrite

1:15 — Switch to Batch mode
        "Recruiters can upload 20 resumes at once and get a ranked shortlist."
        Upload 3 resumes, hit Screen

1:40 — Rankings table appears
        "Each candidate is ranked by score, with the full analysis one click away."

1:55 — "The full code, prompt engineering, and technical decisions
        are on GitHub. Link in the description."
```

### Step 3.4 — After recording
1. In Loom: trim the beginning and end
2. Copy the share link
3. Add to README.md: `📹 **Demo video:** [Loom link]`
4. Add to GitHub repo About: paste the Loom URL

---

## Phase 4 — AI Engineering Work (the important part)

This is what a hiring manager actually wants to see.

### Step 4.1 — Understand the prompt structure

The system prompt in `backend/prompts/analyze_resume.txt` is doing a lot:

**Why we separate the prompt into a file:**
- Easy to iterate without touching Python code
- Shows you think about prompt management as an engineering concern
- Can be version-controlled independently

**Key prompt engineering techniques used:**
1. **Output format specification** — we tell the model EXACTLY what JSON to return
2. **Rubric-based scoring** — we give it explicit score ranges so it's calibrated
3. **Positive examples** — the "weak vs strong bullet" example teaches by example
4. **Negative constraints** — "No markdown. No preamble." prevents common failure modes

### Step 4.2 — Show the structured output pipeline

In `backend/main.py`, the `call_llm_with_retry` function shows three layers:

```python
# Layer 1: Force JSON at the API level
response_format={"type": "json_object"}

# Layer 2: Validate every key exists and has the right type
valid, err = validate_schema(data)

# Layer 3: Regex fallback if model wraps output in markdown
data = extract_json_from_text(raw)
```

This three-layer approach is what separates production LLM code from toy demos.

### Step 4.3 — Commit the prompts folder visibly

```bash
git add backend/prompts/
git commit -m "feat: system prompt with rubric-based scoring and JSON schema"
```

This single commit tells a hiring manager: "this person treats prompts as engineering artifacts."

---

## Phase 5 — Eval Framework

### Step 5.1 — Understand what you're measuring

You're measuring **score calibration**: does the model give similar scores to what
a human recruiter would give?

Not "is the model right" — models will never match humans perfectly.
The question is: is the error small enough to be useful?

### Step 5.2 — Run the existing evals
```bash
cd backend
python evals/run_evals.py
```

This runs 5 test cases and prints accuracy.

### Step 5.3 — Add 15 more cases to reach 20

Open `backend/evals/run_evals.py` and add to `EVAL_DATASET`:
- 4 more strong matches (score 80–95)
- 4 more weak matches (score 10–30)
- 4 moderate matches (score 50–70)
- 3 edge cases (career change, overqualified, missing education)

For each case:
1. Find a real job description on LinkedIn
2. Write a resume text that matches it at a given level
3. Ask 2–3 people what score they'd give it
4. Use the average as your `expected_score`

### Step 5.4 — Add to README

After running evals, add a results section to your README:
```markdown
## Eval results
Model accuracy across 20 annotated resume+JD pairs: **82%**
(within ±10 points of human-annotated score)
```

This is a real signal. Most portfolio projects have no evals at all.

---

## Phase 6 — Retry / Fallback Logic (already in the code)

The `call_llm_with_retry` function in `main.py` implements:

1. **3 retries** on the primary model (LLaMA 3.3 70B)
2. **Exponential backoff** between retries: 1.5s, 2.25s, 3.375s
3. **Model fallback** to LLaMA 3.1 8B if all 3 primary retries fail
4. **3 more retries** on the fallback model
5. **Structured error response** if everything fails (never crashes the API)

To understand why this matters: LLM APIs fail ~2–5% of the time in production.
A production service that crashes on every failure is unusable.
A service that retries gracefully and degrades to a cheaper model is production-grade.

---

## Phase 7 — Streaming (already in the code)

The `/analyze/stream` endpoint in `main.py` uses Server-Sent Events (SSE).

### How to test streaming
```bash
curl -X POST http://localhost:5000/analyze/stream \
  -F "resume=@/path/to/resume.pdf" \
  -F "job_description=Senior Python Engineer..."
```

You'll see tokens stream in real-time.

### How the frontend connects
In `src/lib/api.ts`, `analyzeResumeStream()` opens an SSE connection
and fires callbacks for each event type: `status`, `token`, `result`, `error`, `done`.

The current `SingleAnalyzer.tsx` uses the non-streaming endpoint for simplicity.
To switch to streaming: replace `analyzeResume()` with `analyzeResumeStream()`.

---

## Phase 8 — Batch Analysis (already in the code)

The `/batch` endpoint processes multiple resumes against one JD.

### Key implementation details
1. Files are processed sequentially (not parallel) to avoid rate limits
2. Each file gets the same retry logic as single analysis
3. Results are sorted by `match_score` descending
4. Each result gets a `rank` field (1 = best match)
5. Failed files are collected in an `errors` array (not thrown)

### How to pitch this feature
"Single resume mode is for job seekers. Batch mode is for recruiters —
they can screen 20 candidates in 3 minutes instead of 3 hours."

This doubles your potential user base and is a 20-line backend change.

---

## Phase 9 — LinkedIn Post / Blog (optional but high ROI)

Write a 300-word LinkedIn post titled:
**"I built an AI resume screener in a weekend. Here's what I learned about prompt engineering."**

Cover:
1. The problem (ATS rejection)
2. The tech (Groq + LLaMA 3.3)
3. One technical insight (how you handle malformed JSON)
4. Link to the live demo and GitHub

This takes 30 minutes and signals communication skills — which AI engineer roles increasingly require.

---

## Commit sequence (suggested order)

```bash
# 1 — Working MVP
git commit -m "feat: working MVP - PDF upload, Groq LLM analysis, results UI"

# 2 — Retry logic
git commit -m "feat: retry with exponential backoff and LLaMA 3.1 fallback"

# 3 — Prompt engineering
git commit -m "feat: rubric-based system prompt with JSON schema enforcement"

# 4 — Batch mode
git commit -m "feat: batch analysis endpoint for recruiter use case"

# 5 — Evals
git commit -m "feat: eval framework with 20 annotated test cases"

# 6 — Streaming
git commit -m "feat: SSE streaming endpoint for real-time token display"

# 7 — DECISIONS.md
git commit -m "docs: technical decisions - why Groq, LLaMA 3.3, SSE vs WebSocket"

# 8 — Deploy + demo
git commit -m "chore: deploy to Vercel + Railway, add live demo link"
```

---

## Final checklist

- [ ] Backend runs locally: `python main.py`
- [ ] Frontend runs locally: `npm run dev`
- [ ] Full analysis works end-to-end
- [ ] Backend deployed to Railway
- [ ] Frontend deployed to Vercel
- [ ] Live demo URL in README
- [ ] Loom demo video recorded and linked
- [ ] `backend/prompts/` folder committed and visible
- [ ] `docs/DECISIONS.md` committed
- [ ] Evals run and accuracy documented in README
- [ ] Batch mode tested with 3+ resumes
- [ ] Scanned PDF rejection tested

When all boxes are checked: this is a strong AI engineering portfolio project.
