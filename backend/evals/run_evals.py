"""
Evaluation framework for AI Resume Screener
Run: python evals/run_evals.py

This measures how accurately the LLM scores resumes compared to
ground-truth human-annotated scores. This is the eval dataset approach.
"""

import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import call_llm_with_retry

# ─────────────────────────────────────────────
# GROUND TRUTH DATASET
# 20 resume+JD pairs with human-annotated expected scores
# Format: (resume_text, job_description, expected_score, tolerance)
# tolerance = how many points off we allow and still pass
# ─────────────────────────────────────────────

EVAL_DATASET = [
    {
        "id": "eval_001",
        "description": "Senior Python developer vs. Python backend JD — perfect match",
        "resume": """
John Smith | john@email.com | github.com/johnsmith
EXPERIENCE
Senior Backend Engineer, TechCorp (2020–2024)
- Built REST APIs in Python/FastAPI serving 2M daily requests
- Reduced PostgreSQL query latency by 45% via index optimization
- Led migration from monolith to microservices (Docker, Kubernetes)
- Implemented CI/CD pipeline with GitHub Actions, cutting deploy time 60%
SKILLS: Python, FastAPI, Flask, PostgreSQL, Redis, Docker, Kubernetes, AWS
EDUCATION: BS Computer Science, Stanford 2019
        """,
        "job_description": """
Senior Backend Engineer
Required: 3+ years Python, REST API design, PostgreSQL, Docker, AWS
Nice to have: Kubernetes, Redis, FastAPI
        """,
        "expected_score": 90,
        "tolerance": 10,
    },
    {
        "id": "eval_002",
        "description": "Frontend dev vs. Python backend JD — near zero match",
        "resume": """
Sara Lee | sara@email.com
EXPERIENCE
Frontend Developer, StartupCo (2021–2024)
- Built React components for e-commerce dashboard
- Styled UI with Tailwind CSS and Figma designs
- Integrated Stripe payment UI
SKILLS: React, TypeScript, CSS, Figma, Next.js
        """,
        "job_description": """
Senior Backend Engineer
Required: 3+ years Python, REST API design, PostgreSQL, Docker, AWS
        """,
        "expected_score": 15,
        "tolerance": 15,
    },
    {
        "id": "eval_003",
        "description": "ML engineer vs. data scientist JD — partial match",
        "resume": """
Alex Chen | alex@email.com
EXPERIENCE
ML Engineer, AI Labs (2022–2024)
- Trained computer vision models (PyTorch) for defect detection
- Deployed models to AWS SageMaker, serving 500K predictions/day
- Wrote Python ETL pipelines with pandas and Airflow
SKILLS: Python, PyTorch, TensorFlow, pandas, SQL, AWS SageMaker, Airflow
        """,
        "job_description": """
Data Scientist
Required: Statistical analysis, R or Python, A/B testing, SQL, business intelligence
Nice to have: Machine learning, experiment design
        """,
        "expected_score": 55,
        "tolerance": 15,
    },
    {
        "id": "eval_004",
        "description": "DevOps engineer vs. DevOps JD — strong match",
        "resume": """
Maria Garcia | maria@email.com
EXPERIENCE
DevOps Engineer, CloudBase (2019–2024)
- Managed Kubernetes clusters serving 50+ microservices
- Automated infrastructure with Terraform on AWS (EC2, RDS, S3, CloudFront)
- Built GitHub Actions CI/CD pipelines for 12 engineering teams
- Reduced cloud costs by 30% via right-sizing and spot instances
SKILLS: Kubernetes, Docker, Terraform, AWS, GitHub Actions, Prometheus, Grafana
        """,
        "job_description": """
Senior DevOps Engineer
Required: Kubernetes, Terraform, AWS, CI/CD pipelines, containerization
Nice to have: Prometheus, Grafana, cost optimization experience
        """,
        "expected_score": 88,
        "tolerance": 10,
    },
    {
        "id": "eval_005",
        "description": "Junior dev with 1 year vs. senior role requiring 5+ years",
        "resume": """
Jamie Park | jamie@email.com
EXPERIENCE
Junior Software Developer, WebCo (2023–2024)
- Built CRUD features in Django for internal tools
- Fixed bugs and wrote unit tests
SKILLS: Python, Django, HTML, CSS, Git
EDUCATION: BS CS 2023
        """,
        "job_description": """
Principal Software Engineer
Required: 5+ years experience, system design, team leadership, distributed systems
        """,
        "expected_score": 20,
        "tolerance": 15,
    },
]

# Add 15 more entries for a full dataset of 20
# (abbreviated here — in your real project, fill all 20)

# ─────────────────────────────────────────────
# EVAL RUNNER
# ─────────────────────────────────────────────

def run_evals(dataset=EVAL_DATASET, verbose=True):
    results = []
    passed = 0
    failed = 0

    print(f"\n{'='*60}")
    print(f"Running {len(dataset)} evals...")
    print(f"{'='*60}\n")

    for eval_case in dataset:
        try:
            output = call_llm_with_retry(
                eval_case["resume"],
                eval_case["job_description"],
            )

            actual_score = output.get("match_score", -1)
            expected = eval_case["expected_score"]
            tolerance = eval_case["tolerance"]
            diff = abs(actual_score - expected)
            test_passed = diff <= tolerance

            result = {
                "id": eval_case["id"],
                "description": eval_case["description"],
                "expected": expected,
                "actual": actual_score,
                "diff": diff,
                "tolerance": tolerance,
                "passed": test_passed,
                "recommendation": output.get("recommendation"),
                "model_used": output.get("model_used"),
            }
            results.append(result)

            if test_passed:
                passed += 1
                status = "✅ PASS"
            else:
                failed += 1
                status = "❌ FAIL"

            if verbose:
                print(f"{status} | {eval_case['id']}")
                print(f"       {eval_case['description']}")
                print(f"       Expected: {expected} ± {tolerance} | Got: {actual_score} | Diff: {diff}")
                print()

        except Exception as e:
            failed += 1
            results.append({
                "id": eval_case["id"],
                "passed": False,
                "error": str(e),
            })
            print(f"❌ ERROR | {eval_case['id']}: {e}\n")

    accuracy = (passed / len(dataset)) * 100
    print(f"{'='*60}")
    print(f"Results: {passed}/{len(dataset)} passed ({accuracy:.1f}% accuracy)")
    print(f"{'='*60}\n")

    # Save results to JSON
    output_path = os.path.join(os.path.dirname(__file__), "eval_results.json")
    with open(output_path, "w") as f:
        json.dump({
            "accuracy_pct": accuracy,
            "passed": passed,
            "failed": failed,
            "total": len(dataset),
            "results": results,
        }, f, indent=2)
    print(f"Results saved to {output_path}")

    return accuracy, results


if __name__ == "__main__":
    run_evals()
