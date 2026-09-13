# app/agents/resume_generator.py

import anthropic
from app.models import JobRequirementEvidenceMap, CandidateProfile

client = anthropic.Anthropic()


def generate_resume(
    evidence_map: JobRequirementEvidenceMap,
    profile: CandidateProfile,
    base_resume_path: str = "data/base_resume.md",
) -> str:
    """
    Tailors the candidate's existing resume to the target JD.
    Uses evidence map to know what to emphasise.
    Keeps all real metrics and achievements.
    Never invents new experience.
    """

    # Read base resume
    with open(base_resume_path) as f:
        base_resume = f.read()

    # Build evidence summary
    evidence_summary = "\n".join(
        [
            f"REQUIREMENT: {m.requirement.text} "
            f"({m.requirement.importance.value})\n"
            f"EVIDENCE: {', '.join(m.evidence) if m.evidence else 'none'}\n"
            f"CONFIDENCE: {m.confidence}\n"
            f"GAP: {m.gap}\n"
            for m in evidence_map.matches
        ]
    )

    # Project GitHub URLs
    project_urls = "\n".join(
        [f"{p.name}: {p.github_url or 'no url'}" for p in profile.projects]
    )

    # Extract JD keywords for ATS
    all_keywords = []
    for m in evidence_map.matches:
        all_keywords.extend(m.requirement.keywords)
    keywords_str = ", ".join(set(all_keywords))

    prompt = f"""
You are an expert resume writer helping tailor a resume for a specific job.

TARGET ROLE: {evidence_map.job_title} at {evidence_map.company}

CANDIDATE'S EXISTING RESUME:
{base_resume}

EVIDENCE MAP — what matches this JD:
{evidence_summary}

ATS KEYWORDS TO WEAVE IN NATURALLY: {keywords_str}

PROJECT GITHUB URLS (use these exactly in project sections):
{project_urls}

YOUR TASK:
Tailor the existing resume for this specific role.

RULES:
1. Keep all real metrics EXACTLY as written
   (94% accuracy, faithfulness 0.955, $0.018 per run etc.)
2. Rewrite the summary to mention the target role
   and company domain specifically
3. Reorder projects — strongest match to this JD first
4. Weave JD keywords into bullets where they fit naturally
   Do not keyword stuff — it must read naturally
5. Keep all real experience — do not remove anything
6. Do NOT invent new achievements or metrics
7. Every bullet must come from the existing resume
8. Emphasise experience most relevant to this JD
9. Use exact GitHub URLs provided above for each project
10. Return clean Markdown only
    No explanation, no commentary

TAILORING FOCUS:
- Requirements with high confidence → emphasise these
- Requirements with gaps → do not make up evidence
- Must-have requirements → ensure they appear prominently

Return the complete tailored resume in Markdown.
"""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.content[0].text.strip()
