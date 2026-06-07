 
import os
import re
import json
import tempfile
import logging
from pathlib import Path

import pdfplumber
from groq import Groq
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# ── Setup ─────────────────────────────────────────────────────────────────────

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MAX_PDF_SIZE_MB = 5

# ── PDF Extraction ─────────────────────────────────────────────────────────────

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name

    try:
        full_text = []
        with pdfplumber.open(tmp_path) as pdf:
            if len(pdf.pages) == 0:
                raise ValueError("The PDF has no pages.")
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text.append(text.strip())
    except Exception as e:
        raise ValueError(f"Could not read PDF: {str(e)}")
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    combined = "\n\n".join(full_text).strip()

    if len(combined) < 100:
        raise ValueError(
            "PDF appears to be a scanned image or has no readable text. "
            "Please upload a text-based PDF — export directly from Word or Google Docs."
        )

    return combined


def clean_resume_text(raw: str) -> str:
    text = raw.replace("\x00", "")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


# ── LLM Analysis ──────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert technical recruiter and resume coach with 15 years of experience hiring for AI, software engineering, and data science roles.

Analyze a resume against a job description and return structured, actionable feedback.

CRITICAL RULES:
- Return ONLY valid JSON. No markdown, no preamble, no explanation outside the JSON.
- Match the schema exactly. No extra keys, no missing keys.
- All string values must be plain text — no markdown inside JSON strings.
- The "rewrite" must be a concrete, specific improved bullet — not vague advice.
- "missing_keywords" must be actual terms from the JD absent from the resume.
- "match_score" must be an integer 0–100.
- Provide at least 2 and at most 4 weak_sections.
- Provide at least 3 missing_keywords and at least 3 strengths.

SCHEMA (return exactly this structure):
{
  "match_score": <integer 0-100>,
  "verdict": "<one word: Excellent | Strong | Moderate | Weak>",
  "summary": "<2 sentence plain English verdict on the overall fit>",
  "strengths": ["<matching skill or keyword>"],
  "missing_keywords": ["<keyword from JD missing in resume>"],
  "weak_sections": [
    {
      "section": "<e.g. Experience — Intern at XYZ>",
      "issue": "<specific problem: no metrics / vague / missing keyword>",
      "original": "<exact weak text from resume>",
      "rewrite": "<concrete rewrite with impact, metrics, and relevant keywords>"
    }
  ],
  "top_recommendation": "<single most important action the candidate should take>"
}

SCORING:
85–100: Excellent — apply immediately
70–84:  Strong — minor gaps
50–69:  Moderate — significant missing requirements
0–49:   Weak — major skill or experience gaps"""


def build_user_prompt(resume_text: str, job_description: str) -> str:
    return f"""RESUME:
{resume_text[:4000]}

JOB DESCRIPTION:
{job_description[:2000]}

Analyze the resume against the job description and return the JSON."""


def parse_llm_response(raw: str) -> dict:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        log.error("LLM returned invalid JSON: %s\nRaw: %s", e, raw[:500])
        raise ValueError("The AI returned an unexpected response. Please try again.")

    required = {"match_score", "verdict", "summary", "strengths",
                "missing_keywords", "weak_sections", "top_recommendation"}
    missing = required - set(data.keys())
    if missing:
        raise ValueError(f"Analysis incomplete — missing fields: {', '.join(missing)}")

    data["match_score"] = max(0, min(100, int(data.get("match_score", 0))))
    return data


def analyze_with_groq(resume_text: str, job_description: str) -> dict:
    log.info("Sending request to Groq LLaMA 3.3 70B...")
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": build_user_prompt(resume_text, job_description)},
            ],
            temperature=0.2,
            max_tokens=2048,
        )
    except Exception as e:
        log.error("Groq API error: %s", e)
        raise RuntimeError("AI service temporarily unavailable. Please try again.")

    raw = response.choices[0].message.content
    log.info("Groq response received (%d chars)", len(raw))
    return parse_llm_response(raw)


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "model": "llama-3.3-70b-versatile"})


@app.route("/analyze", methods=["POST"])
def analyze():
    # Validate file
    if "resume" not in request.files:
        return jsonify({"error": "No resume file uploaded. Please attach a PDF."}), 400

    file = request.files["resume"]
    job_description = request.form.get("job_description", "").strip()

    if not file.filename:
        return jsonify({"error": "Empty filename. Please re-upload your resume."}), 400

    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are supported."}), 400

    if not job_description:
        return jsonify({"error": "Job description is required."}), 400

    if len(job_description) < 50:
        return jsonify({"error": "Job description too short. Paste the complete job posting."}), 400

    # File size check
    pdf_bytes = file.read()
    size_mb = len(pdf_bytes) / (1024 * 1024)
    if size_mb > MAX_PDF_SIZE_MB:
        return jsonify({"error": f"PDF too large ({size_mb:.1f}MB). Max is {MAX_PDF_SIZE_MB}MB."}), 413

    # Extract text
    try:
        raw_text = extract_text_from_pdf(pdf_bytes)
        resume_text = clean_resume_text(raw_text)
        log.info("Extracted %d characters from PDF", len(resume_text))
    except ValueError as e:
        return jsonify({"error": str(e)}), 422

    # LLM analysis
    try:
        result = analyze_with_groq(resume_text, job_description)
    except ValueError as e:
        return jsonify({"error": str(e)}), 502
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503

    log.info(
        "Done — score: %d | missing: %d | rewrites: %d",
        result.get("match_score", 0),
        len(result.get("missing_keywords", [])),
        len(result.get("weak_sections", [])),
    )
    return jsonify(result), 200


# ── Error handlers ─────────────────────────────────────────────────────────────

@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": f"File too large. Max {MAX_PDF_SIZE_MB}MB."}), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found. Use POST /analyze or GET /health"}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed. Use POST /analyze"}), 405


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not os.getenv("GROQ_API_KEY"):
        log.warning("⚠️  GROQ_API_KEY not set — add it to backend/.env")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("FLASK_ENV", "production") == "development"
    log.info("🚀 Starting on port %d (debug=%s)", port, debug)
    app.run(host="0.0.0.0", port=port, debug=debug)