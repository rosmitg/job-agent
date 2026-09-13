# app/agents/revision_loop.py

import anthropic
from app.models import JobRequirementEvidenceMap, CandidateProfile
from app.agents.resume_generator import generate_resume
from app.agents.evaluator import evaluate_resume

client = anthropic.Anthropic()

MAX_REVISIONS = 2


def revise_resume(
    resume: str,
    failures: list[str],
    recommendation: str,
    evidence_map: JobRequirementEvidenceMap,
    profile: CandidateProfile,
    base_resume: str,
) -> str:
    """
    Takes a resume that failed evaluation.
    Uses failures and recommendation as
    external feedback to generate a better version.
    """
    failures_str = "\n".join([f"- {f}" for f in failures])

    prompt = f"""
You are an expert resume writer revising a resume.

The previous version failed quality checks.
Fix ONLY the issues listed below.
Do not change anything else.

ISSUES TO FIX:
{failures_str}

RECOMMENDATION:
{recommendation}

TARGET ROLE: {evidence_map.job_title} at {evidence_map.company}

RESUME TO REVISE:
{resume}

BASE RESUME FOR REFERENCE:
{base_resume}

REVISION RULES:
1. Fix only the listed issues
2. Keep all real metrics exactly as written
3. Keep all real experience
4. Do not invent new content
5. Return clean Markdown only
"""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.content[0].text.strip()


def run_revision_loop(
    evidence_map: JobRequirementEvidenceMap,
    profile: CandidateProfile,
    base_resume_path: str = "data/base_resume.md",
) -> dict:
    """
    Full pipeline with revision loop.

    Generate → Evaluate → Revise if needed
    Max 2 revisions then return best version.
    """
    with open(base_resume_path) as f:
        base_resume = f.read()

    # Generate V1
    print("Generating resume V1...")
    resume = generate_resume(evidence_map, profile, base_resume_path)

    best_resume = resume
    best_score = 0
    revision_count = 0

    while revision_count <= MAX_REVISIONS:
        print(f"\nEvaluating (attempt {revision_count + 1})...")
        result = evaluate_resume(resume, evidence_map, base_resume)

        # Track best version by total subjective score
        current_score = result["subjective"]["total"]
        if current_score > best_score:
            best_score = current_score
            best_resume = resume

        if result["passed"]:
            print(f"✅ Passed on attempt {revision_count + 1}")
            return {
                "resume": resume,
                "evaluation": result,
                "revisions": revision_count,
                "passed": True,
            }

        # Failed — revise if budget remaining
        if revision_count < MAX_REVISIONS:
            print(
                f"❌ Failed — revising (attempt {revision_count + 1}/{MAX_REVISIONS})"
            )
            print("Failures:")
            for f in result["failures"]:
                print(f"  - {f}")

            resume = revise_resume(
                resume=resume,
                failures=result["failures"],
                recommendation=result["subjective"]["recommendation"],
                evidence_map=evidence_map,
                profile=profile,
                base_resume=base_resume,
            )
        else:
            print(f"⚠️  Max revisions reached — returning best version")
            break

        revision_count += 1

    return {
        "resume": best_resume,
        "evaluation": result,
        "revisions": revision_count,
        "passed": False,
    }
