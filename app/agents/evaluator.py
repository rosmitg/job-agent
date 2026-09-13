# app/agents/evaluator.py

import json
import anthropic
from app.models import JobRequirementEvidenceMap

client = anthropic.Anthropic()

# ─────────────────────────────────────────
# Programmatic checks — no LLM needed
# ─────────────────────────────────────────


def check_programmatic(
    resume: str, evidence_map: JobRequirementEvidenceMap, base_resume: str
) -> dict:
    """
    Objective checks using Python only.
    Fast, free, consistent.
    """
    resume_lower = resume.lower()

    # 1. Seniority check — did it embellish?
    embellished = "aspiring" in base_resume.lower() and "aspiring" not in resume_lower

    # 2. Graduation check
    wrong_graduation = (
        "currently completing" in resume_lower or "currently pursuing" in resume_lower
    )

    # 3. JD keyword coverage
    all_keywords = []
    for m in evidence_map.matches:
        all_keywords.extend(m.requirement.keywords)

    keywords_found = [kw for kw in all_keywords if kw.lower() in resume_lower]
    keyword_coverage = len(keywords_found) / len(all_keywords) if all_keywords else 1.0

    # 4. Real metrics preserved
    key_metrics = ["0.955", "0.900", "94%", "4.88", "0.018", "0.009"]
    metrics_present = [m for m in key_metrics if m in resume]
    metrics_coverage = len(metrics_present) / len(key_metrics)

    # 5. Word count
    word_count = len(resume.split())
    acceptable_length = 400 <= word_count <= 800

    return {
        "embellished_seniority": embellished,
        "wrong_graduation_status": wrong_graduation,
        "keyword_coverage": round(keyword_coverage, 2),
        "metrics_coverage": round(metrics_coverage, 2),
        "word_count": word_count,
        "acceptable_length": acceptable_length,
        "keywords_found": keywords_found,
        "metrics_found": metrics_present,
    }


# ─────────────────────────────────────────
# LLM-as-judge — subjective checks
# ─────────────────────────────────────────


def check_subjective(resume: str, evidence_map: JobRequirementEvidenceMap) -> dict:
    """
    Subjective quality checks using LLM-as-judge.
    Rubric-based scoring — consistent and traceable.
    """
    prompt = f"""
You are an expert recruiter evaluating a tailored resume.

TARGET ROLE: {evidence_map.job_title} at {evidence_map.company}

RESUME TO EVALUATE:
{resume}

Score the resume on each criterion from 1 to 5.
Be honest and strict.

RUBRIC:

1. Honesty (1-5):
   Does the resume make claims that seem inflated or invented?
   1 = multiple false or inflated claims
   3 = mostly honest with minor stretches
   5 = completely honest, every claim believable

2. Relevance (1-5):
   How well does the resume match the target role?
   1 = mostly irrelevant experience shown
   3 = some relevant experience highlighted
   5 = most relevant experience prominently featured

3. Specificity (1-5):
   Are bullets specific with real metrics and outcomes?
   1 = vague bullets with no metrics
   3 = some specific bullets
   5 = every bullet specific with real numbers

4. Clarity (1-5):
   Is the resume easy to read and well structured?
   1 = hard to follow, poor structure
   3 = readable but could be cleaner
   5 = clear, professional, easy to scan

5. ATS Friendliness (1-5):
   Does it naturally include relevant keywords?
   1 = missing most keywords
   3 = some keywords included
   5 = all key terms naturally woven in

Return ONLY valid JSON:
{{
    "honesty": <1-5>,
    "relevance": <1-5>,
    "specificity": <1-5>,
    "clarity": <1-5>,
    "ats_friendliness": <1-5>,
    "total": <sum of all five>,
    "weakest_area": "<which criterion scored lowest>",
    "recommendation": "<one specific thing to improve>"
}}"""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )

    content = response.content[0].text.strip()
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()

    return json.loads(content)


# ─────────────────────────────────────────
# Quality gate
# ─────────────────────────────────────────


def check_quality_gate(programmatic: dict, subjective: dict) -> tuple[bool, list[str]]:
    """
    Decides if resume passes or needs revision.
    Same concept as your RAGAS CI gate and
    email regression detector blocking threshold.
    """
    failures = []

    # Hard failures — must fix
    if programmatic["embellished_seniority"]:
        failures.append("Seniority embellished — restore 'aspiring' framing")

    if programmatic["wrong_graduation_status"]:
        failures.append("Graduation status wrong — you graduated July 2025")

    if programmatic["keyword_coverage"] < 0.6:
        failures.append(
            f"Low keyword coverage: "
            f"{programmatic['keyword_coverage']:.0%} "
            f"— weave in more JD keywords"
        )

    if programmatic["metrics_coverage"] < 0.5:
        failures.append(
            f"Key metrics missing — "
            f"only {len(programmatic['metrics_found'])} "
            f"of {len(['0.955','0.900','94%','4.88','0.018','0.009'])} "
            f"found"
        )

    # Subjective failures
    if subjective["honesty"] < 3:
        failures.append(
            f"Honesty score too low: {subjective['honesty']}/5 "
            f"— resume may contain inflated claims"
        )

    if subjective["total"] < 18:
        failures.append(
            f"Overall quality too low: {subjective['total']}/25 "
            f"— {subjective['recommendation']}"
        )

    passed = len(failures) == 0
    return passed, failures


# ─────────────────────────────────────────
# Main evaluate function
# ─────────────────────────────────────────


def evaluate_resume(
    resume: str, evidence_map: JobRequirementEvidenceMap, base_resume: str
) -> dict:
    """
    Full evaluation combining programmatic
    and subjective checks.
    Returns scores and pass/fail decision.
    """
    print("Running programmatic checks...")
    programmatic = check_programmatic(resume, evidence_map, base_resume)

    print("Running LLM-as-judge scoring...")
    subjective = check_subjective(resume, evidence_map)

    print("Checking quality gate...")
    passed, failures = check_quality_gate(programmatic, subjective)

    return {
        "passed": passed,
        "failures": failures,
        "programmatic": programmatic,
        "subjective": subjective,
    }
