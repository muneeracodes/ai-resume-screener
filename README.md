# AI Resume Screener

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Flask](https://img.shields.io/badge/Flask-3.1-green)
![Groq](https://img.shields.io/badge/Groq-LLaMA%203.3-purple)
![React](https://img.shields.io/badge/React-Vite-61DAFB)
![Status](https://img.shields.io/badge/Status-In%20Development-orange)

AI-powered resume analysis tool that scores your resume against a job
description, identifies missing keywords, and rewrites weak bullet points
using Groq LLaMA 3.3 70B.

🔗 **Live demo:** Coming soon
📹 **Demo video:** Coming soon

---

## The problem

Job seekers spend hours guessing why their resume isn't getting callbacks.
ATS systems reject 75% of resumes before a human sees them — usually
because of missing keywords, not missing skills. This tool gives instant,
specific, actionable feedback in under 30 seconds.

---

## System architecture

PDF Upload (React)
│
▼
Flask Backend (Python)
│
├─► pdfplumber — text extraction + cleaning
│
└─► Groq LLaMA 3.3 70B — structured analysis
└─ outputs: match_score, missing_keywords,
strengths, weak_sections with rewrites


## Tech stack

| Layer       | Technology                         |
|-------------|------------------------------------|
| Frontend    | React · Vite · Tailwind CSS        |
| Backend     | Flask · Python 3.11                |
| LLM         | Groq API · LLaMA 3.3 70B          |
| PDF parsing | pdfplumber                         |
| Deployment  | Vercel (frontend) · Railway (backend) |

## Features

- Upload any PDF resume and receive analysis in under 30 seconds
- Match score (0–100) with colour-coded rating
- Missing keyword detection from the job description
- Bullet point rewriter — before/after cards with specific improvements
- Scanned PDF detection with user-friendly error messages

## Project status

🚧 **Actively building** — started June 2026

- [x] Project scaffold
- [ ] PDF extraction pipeline
- [ ] Groq LLM integration
- [ ] React frontend
- [ ] Deployment

## Local setup

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your GROQ_API_KEY
python main.py

# Frontend
cd frontend
npm install && npm run dev
```

---

Built by [Muneera Ibrahim](https://github.com/muneeracodes)