# main.py
# Single entry point for the job application agent.
# Paste a JD, get a tailored resume.

from app.agents.jd_parser import parse_jd
from app.agents.profile_loader import load_profile
from app.agents.evidence_matcher import match_evidence, check_filter_gate
from app.agents.revision_loop import run_revision_loop


def run(jd_text: str):
    print("\n" + "=" * 50)
    print("JOB APPLICATION AGENT")
    print("=" * 50)

    # Step 1: Parse JD
    print("\n📋 Step 1: Parsing job description...")
    jd = parse_jd(jd_text)
    print(f"Role: {jd.job_title} at {jd.company_name}")
    print(f"Seniority: {jd.seniority}")
    print(f"Requirements found: {len(jd.requirements)}")

    # Step 2: Load profile
    print("\n👤 Step 2: Loading candidate profile...")
    profile = load_profile()
    print(f"Loaded: {profile.name}")

    # Step 3: Match evidence
    print("\n🔍 Step 3: Matching evidence...")
    evidence_map = match_evidence(jd, profile)
    print(f"Coverage: {evidence_map.coverage_score:.0%}")
    print(f"Must-have coverage: {evidence_map.must_have_coverage:.0%}")

    for match in evidence_map.matches:
        status = "❌ GAP" if match.gap else "✅ OK"
        print(
            f"  {status} [{match.requirement.importance.value}] "
            f"{match.requirement.text} "
            f"(confidence: {match.confidence})"
        )

    # Step 4: Filter gate
    print("\n🚦 Step 4: Checking filter gate...")
    passed, reasons = check_filter_gate(evidence_map)

    if not passed:
        print("❌ FILTER GATE FAILED — do not apply to this role")
        for r in reasons:
            print(f"  {r}")
        return None

    print("✅ Filter gate passed — proceeding to resume generation")

    # Step 5: Generate and evaluate
    print("\n✍️  Step 5: Generating tailored resume...")
    result = run_revision_loop(evidence_map, profile)

    print(f"\n📊 Evaluation:")
    print(f"  Passed:    {result['passed']}")
    print(f"  Revisions: {result['revisions']}")
    print(f"  Score:     {result['evaluation']['subjective']['total']}/25")
    print(f"  Weakest:   {result['evaluation']['subjective']['weakest_area']}")

    # Step 6: Save output
    output_path = f"output_{jd.company_name.lower().replace(' ', '_')}_resume.md"
    with open(output_path, "w") as f:
        f.write(result["resume"])

    print(f"\n✅ Resume saved to {output_path}")
    print("\n" + "=" * 50)
    print("HUMAN REVIEW REQUIRED")
    print("=" * 50)
    print("Review the generated resume before submitting.")
    print("Check all claims are accurate and honest.")
    print(f"File: {output_path}")

    return result


if __name__ == "__main__":
    jd_text = """
    AI Engineer at Westpac Sydney.
    Must have Python and LangChain.
    Must have Australian work rights.
    Preferred: Docker, AWS.
    Full time graduate role.
    Build RAG systems for banking.
    """

    run(jd_text)
