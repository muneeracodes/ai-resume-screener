# Technical Decisions

This document explains the "why" behind every major technical choice in this project.
Hiring managers and senior engineers care about decisions, not just implementation.

---

## Why Groq over OpenAI?

| Factor | Groq | OpenAI |
|--------|------|--------|
| Latency | ~200ms per token (custom LPU hardware) | ~800ms per token |
| Free tier | 14,400 requests/day | Very limited |
| Cost | ~$0.59 per 1M tokens | ~$3.00+ per 1M tokens |
| Open models | LLaMA, Mixtral, Gemma | GPT-4o (proprietary) |

**Decision**: For a portfolio project where response speed is the core UX, Groq's inference speed
is a meaningful differentiator. A resume analysis that finishes in 8 seconds vs. 25 seconds
is the difference between a good and bad demo. Groq also lets us use open-weight models,
which is a better portfolio signal than just calling OpenAI.

---

## Why LLaMA 3.3 70B over LLaMA 3.1?

| Factor | LLaMA 3.3 70B | LLaMA 3.1 70B |
|--------|---------------|---------------|
| Instruction following | Significantly better | Good |
| JSON output reliability | Higher | Moderate |
| Context window | 128K tokens | 128K tokens |
| Training cutoff | Later (2024) | Earlier |

**Decision**: LLaMA 3.3 70B is Meta's newest 70B-class model at the time of building. For our use case —
returning reliably structured JSON with consistent formatting — the improved instruction-following
in 3.3 measurably reduces malformed output (tested in evals). We use 3.1 8B as the **fallback**
because it's faster and cheaper when we just need a basic parse on retry.

**Fallback chain**: LLaMA 3.3 70B → (retry 3x) → LLaMA 3.1 8B → (retry 3x) → structured error.

---

## Why structured output (JSON mode) over free-form text?

The original naive approach would be: "analyze this resume and tell me what you think."
That produces good prose but is unparseable by the frontend.

Production LLM integration requires:
1. `response_format: {"type": "json_object"}` — forces the model to produce valid JSON
2. An explicit JSON schema in the system prompt — ensures key names match what our code expects
3. A validation layer (`validate_schema()`) — catches cases where the model omits keys
4. A regex fallback (`extract_json_from_text()`) — handles markdown fences that some models add

This three-layer approach is what separates a toy demo from production LLM code.

---

## Why retry with exponential backoff?

LLM APIs fail in two ways:
1. **Rate limits** — handled by slowing down (backoff: 1.5s, 2.25s, 3.375s)
2. **Malformed output** — handled by retrying with the same prompt (the model may produce valid
   JSON on a second attempt at temperature 0.2)

Exponential backoff prevents hammering the API when it's already under load.
The multiplier is 1.5x (lighter than the classic 2x) because Groq's rate limits reset quickly.

---

## Why Flask over FastAPI?

FastAPI would be the "correct" modern answer for a new Python API. Flask is chosen here because:

1. The project already has Flask in the scaffold
2. Flask's simplicity makes the AI engineering code easier to read (fewer decorators, less magic)
3. For a portfolio project, the LLM integration patterns are what matter, not the framework

**If this were production**: FastAPI with async endpoints and Pydantic models for schema validation
would be the better choice. The patterns (retry logic, streaming, structured output) are identical.

---

## Why pdfplumber over PyPDF2?

pdfplumber uses a more robust text extraction engine (pdfminer under the hood) and handles:
- Multi-column layouts
- Tables
- Complex formatting

PyPDF2 often drops whitespace and mangles formatting in these cases.
For resumes — which are often two-column or heavily formatted — this matters.

---

## Streaming: SSE vs WebSocket

Server-Sent Events (SSE) is chosen over WebSockets because:
- SSE is unidirectional (server → client only), which is all we need for streaming tokens
- SSE works over standard HTTP — no upgrade handshake, simpler to deploy
- Vercel and Railway both support SSE without configuration
- WebSockets require a persistent connection and more complex CORS handling

---

## Eval design philosophy

The eval dataset tests **calibration**, not just correctness:
- A model that scores every resume 75 would pass correctness tests but fail calibration
- We test the score against a human-annotated expected score with a tolerance band (±10-15 points)
- We cover the full score range: perfect matches, partial matches, wrong field, experience mismatch

This is how ML teams measure LLM quality in production.
