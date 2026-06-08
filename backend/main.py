"""
AI Resume Screener — Flask Backend
Features: PDF parsing, Groq LLM integration, structured JSON output,
retry/fallback logic, streaming, batch analysis
"""

import os
import json
import time
import re
import logging
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import pdfplumber
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173", os.getenv("FRONTEND_URL", "")])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ─────────────────────────────────────────────
# PROMPTS  (loaded from prompts/ folder)
# ─────────────────────────────────────────────

def load_prompt(name: str) -> str:
    path = os.path.join(os.path.dirname(__file__), "prompts", f"{name}.txt")
    with open(path) as f:
        return f.read()

# ─────────────────────────────────────────────
# PDF EXTRACTION
# ─────────────────────────────────────────────

def extract_pdf_text(file_bytes: bytes) -> tuple[str, bool]:
    """
    Returns (text, is_scanned).
    Scanned PDFs have images but no selectable text — we detect and reject them.
    """
    import io
    text_blocks = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                text_blocks.append(text)

    full_text = "\n".join(text_blocks).strip()

    # If text is suspiciously short relative to page count, it is likely scanned
    is_scanned = len(full_text) < 100
    return full_text, is_scanned

# ─────────────────────────────────────────────
# STRUCTURED JSON PARSING WITH RETRY + FALLBACK
# ─────────────────────────────────────────────

EXPECTED_SCHEMA = {
    "match_score": int,
    "score_rationale": str,
    "missing_keywords": list,
    "strengths": list,
    "weak_sections": list,
    "recommendation": str,
}

def clean_and_heal_data(data: dict) -> dict:
    """
    Normalizes and heals common LLM generation variance so that
    it is guaranteed to match the exact frontend typescript structures.
    """
    # 1. Self-healing key maps for similar semantic expressions
    mappings = {
        "justification": "score_rationale",
        "rationale": "score_rationale",
        "missing_skills": "missing_keywords",
        "keyword_gaps": "missing_keywords",
        "aligned_strengths": "strengths",
        "found_keywords": "strengths",
        "recommended_rewrites": "weak_sections"
    }
    
    for old_key, new_key in mappings.items():
        if old_key in data and new_key not in data:
            data[new_key] = data[old_key]

    # Ensure all baseline keys are initialized with safe default types if completely absent
    if "match_score" not in data:
        data["match_score"] = 0
    else:
        # Cast match_score to integer if returned as a string or float
        try:
            data["match_score"] = int(float(data["match_score"]))
        except (ValueError, TypeError):
            data["match_score"] = 0

    if "score_rationale" not in data or not isinstance(data["score_rationale"], str):
        data["score_rationale"] = "No rationale provided."

    if "missing_keywords" not in data or not isinstance(data["missing_keywords"], list):
        data["missing_keywords"] = []

    if "strengths" not in data or not isinstance(data["strengths"], list):
        data["strengths"] = []

    if "weak_sections" not in data or not isinstance(data["weak_sections"], list):
        data["weak_sections"] = []

    # Parse and structural check elements in weak_sections
    healed_sections = []
    for section in data["weak_sections"]:
        if isinstance(section, dict):
            # Repair nested keys inside weak_sections
            original = str(section.get("original", section.get("current_text", "Section improvement needed.")))
            rewrite = str(section.get("rewrite", section.get("suggested_rewrite", "")))
            reason = str(section.get("reason", section.get("explanation", "Needs optimization.")))
            healed_sections.append({
                "original": original,
                "rewrite": rewrite,
                "reason": reason
            })
    data["weak_sections"] = healed_sections

    if "recommendation" not in data:
        # Generate dynamically if missing based on match_score
        score = data["match_score"]
        if score >= 80:
            data["recommendation"] = "strong_match"
        elif score >= 50:
            data["recommendation"] = "moderate_match"
        elif score >= 25:
            data["recommendation"] = "weak_match"
        else:
            data["recommendation"] = "no_match"
            
    # Normalize recommendation string syntax
    rec = str(data["recommendation"]).lower().replace(" ", "_")
    valid_recs = ["strong_match", "moderate_match", "weak_match", "no_match"]
    if rec not in valid_recs:
        data["recommendation"] = "moderate_match"
    else:
        data["recommendation"] = rec

    return data
def validate_schema(data: dict) -> tuple[bool, str]:
    """Check every required key exists and has the right type."""
    for key, expected_type in EXPECTED_SCHEMA.items():
        if key not in data:
            return False, f"Missing key: {key}"
        if not isinstance(data[key], expected_type):
            return False, f"Wrong type for {key}: expected {expected_type.__name__}"
    if not (0 <= data["match_score"] <= 100):
        return False, "match_score must be 0–100"
    return True, ""

def extract_json_from_text(text: str) -> dict | None:
    """Try to extract JSON even if the model wrapped it in markdown fences."""
    # Strip markdown fences
    cleaned = re.sub(r"```(?:json)?", "", text).replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to find the JSON object with regex
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                return None
    return None

def call_llm_with_retry(
    resume_text: str,
    job_description: str,
    max_retries: int = 3,
    model: str = "llama-3.3-70b-versatile",
) -> dict:
    """
    Call Groq LLaMA 3.3 with up to max_retries attempts.
    On failure, tries a fallback model (llama-3.1-8b-instant).
    """
    system_prompt = load_prompt("analyze_resume")
    user_message = f"""
RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}
"""

    models_to_try = [model, "llama-3.1-8b-instant"]

    for model_attempt in models_to_try:
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"LLM call attempt {attempt} with model {model_attempt}")
                response = client.chat.completions.create(
                    model=model_attempt,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    temperature=0.2,   # low temp = more deterministic JSON
                    max_tokens=2000,
                    response_format={"type": "json_object"},  # Groq structured output
                )

                raw = response.choices[0].message.content
                logger.info(f"Raw LLM response: {raw[:200]}...")

                data = extract_json_from_text(raw)
                if data is None:
                    raise ValueError("Could not parse JSON from response")
                data = clean_and_heal_data(data)

                valid, err = validate_schema(data)
                if not valid:
                    raise ValueError(f"Schema validation failed: {err}")

                data["model_used"] = model_attempt
                data["attempts"] = attempt
                return data

            except Exception as e:
                logger.warning(f"Attempt {attempt} failed: {e}")
                if attempt < max_retries:
                    time.sleep(1.5 ** attempt)  # exponential backoff: 1.5s, 2.25s

        logger.warning(f"All retries failed for {model_attempt}, trying fallback...")

    # Hard fallback: return a structured error response
    return {
        "match_score": 0,
        "score_rationale": "Analysis could not be completed. Please try again.",
        "missing_keywords": [],
        "strengths": [],
        "weak_sections": [],
        "recommendation": "error",
        "model_used": "none",
        "attempts": max_retries,
        "error": True,
    }

# ─────────────────────────────────────────────
# STREAMING  (Server-Sent Events)
# ─────────────────────────────────────────────

def stream_analysis(resume_text: str, job_description: str):
    """
    Generator that yields SSE events as the LLM streams tokens.
    The frontend can display results progressively.
    """
    system_prompt = load_prompt("analyze_resume")
    user_message = f"RESUME:\n{resume_text}\n\nJOB DESCRIPTION:\n{job_description}"

    def send(event: str, data: str):
        return f"event: {event}\ndata: {json.dumps(data)}\n\n"

    try:
        yield send("status", "Connecting to LLM...")

        stream = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.2,
            max_tokens=2000,
            stream=True,
        )

        yield send("status", "Analyzing resume...")

        full_response = ""
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            full_response += delta
            if delta:
                yield send("token", delta)

        # Parse and validate the complete response
        data = extract_json_from_text(full_response)
        if data:
            valid, err = validate_schema(data)
            if valid:
                yield send("result", json.dumps(data))
            else:
                yield send("error", f"Schema error: {err}")
        else:
            yield send("error", "Could not parse response")

    except Exception as e:
        logger.error(f"Streaming error: {e}")
        yield send("error", str(e))

    finally:
        yield send("done", "")

# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "model": "llama-3.3-70b-versatile"})


@app.route("/analyze", methods=["POST"])
def analyze():
    """Single resume analysis — returns JSON."""
    if "resume" not in request.files:
        return jsonify({"error": "No resume file uploaded"}), 400

    job_description = request.form.get("job_description", "").strip()
    if not job_description:
        return jsonify({"error": "Job description is required"}), 400

    file = request.files["resume"]
    if not file.filename.endswith(".pdf"):
        return jsonify({"error": "Only PDF files are supported"}), 400

    file_bytes = file.read()
    resume_text, is_scanned = extract_pdf_text(file_bytes)

    if is_scanned:
        return jsonify({
            "error": "scanned_pdf",
            "message": "This PDF appears to be a scanned image. Please upload a text-based PDF.",
        }), 422

    result = call_llm_with_retry(resume_text, job_description)
    return jsonify(result)


@app.route("/analyze/stream", methods=["POST"])
def analyze_stream():
    """Single resume analysis — streams tokens via SSE."""
    if "resume" not in request.files:
        return jsonify({"error": "No resume file uploaded"}), 400

    job_description = request.form.get("job_description", "").strip()
    if not job_description:
        return jsonify({"error": "Job description is required"}), 400

    file = request.files["resume"]
    file_bytes = file.read()
    resume_text, is_scanned = extract_pdf_text(file_bytes)

    if is_scanned:
        return jsonify({"error": "scanned_pdf"}), 422

    return Response(
        stream_with_context(stream_analysis(resume_text, job_description)),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            # ─── ADD THESE TWO LINES FOR CORS STREAM SECURITY ───
            "Access-Control-Allow-Origin": "http://localhost:5173",
            "Access-Control-Allow-Credentials": "true",
        },
    )
    """Single resume analysis — streams tokens via SSE."""
    if "resume" not in request.files:
        return jsonify({"error": "No resume file uploaded"}), 400

    job_description = request.form.get("job_description", "").strip()
    if not job_description:
        return jsonify({"error": "Job description is required"}), 400

    file = request.files["resume"]
    file_bytes = file.read()
    resume_text, is_scanned = extract_pdf_text(file_bytes)

    if is_scanned:
        return jsonify({"error": "scanned_pdf"}), 422

    return Response(
        stream_with_context(stream_analysis(resume_text, job_description)),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.route("/batch", methods=["POST"])
def batch_analyze():
    """
    Batch analysis: multiple resumes vs. one job description.
    Returns ranked list — designed for recruiters.
    """
    job_description = request.form.get("job_description", "").strip()
    if not job_description:
        return jsonify({"error": "Job description is required"}), 400

    files = request.files.getlist("resumes")
    if not files or len(files) == 0:
        return jsonify({"error": "No files uploaded"}), 400
    if len(files) > 20:
        return jsonify({"error": "Maximum 20 resumes per batch"}), 400

    results = []
    errors = []

    for file in files:
        try:
            file_bytes = file.read()
            resume_text, is_scanned = extract_pdf_text(file_bytes)

            if is_scanned:
                errors.append({"filename": file.filename, "error": "scanned_pdf"})
                continue

            analysis = call_llm_with_retry(resume_text, job_description)
            analysis["filename"] = file.filename
            results.append(analysis)

        except Exception as e:
            errors.append({"filename": file.filename, "error": str(e)})

    # Sort by match score descending
    results.sort(key=lambda x: x.get("match_score", 0), reverse=True)

    # Add rank
    for i, r in enumerate(results):
        r["rank"] = i + 1

    return jsonify({
        "total": len(files),
        "successful": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors,
        "job_description_preview": job_description[:200],
    })


if __name__ == "__main__":
    app.run(debug=True, port=8000)
