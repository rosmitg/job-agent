# app/agents/resume_generator.py

import anthropic
from app.models import JobRequirementEvidenceMap, CandidateProfile

client = anthropic.Anthropic()


def generate_resume(
    evidence_map: JobRequirementEvidenceMap,
    profile: CandidateProfile,
    base_resume_path: str = "data/base_resume.md",
    template_path: str = "data/template.tex",
) -> str:
    """
    Generates a tailored LaTeX resume.
    Uses the candidate's LaTeX template as structure.
    Tailors content based on evidence map.
    Every bullet grounded in real evidence.
    """

    with open(base_resume_path) as f:
        base_resume = f.read()

    with open(template_path) as f:
        template = f.read()

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

    project_urls = "\n".join(
        [f"{p.name}: {p.github_url or 'no url'}" for p in profile.projects]
    )

    all_keywords = []
    for m in evidence_map.matches:
        all_keywords.extend(m.requirement.keywords)
    keywords_str = ", ".join(set(all_keywords))

    prompt = f"""
You are an expert resume writer and LaTeX specialist.

You have a candidate's LaTeX resume template and their base resume content.
Your job is to tailor the LaTeX resume for a specific role.

TARGET ROLE: {evidence_map.job_title} at {evidence_map.company}

LATEX TEMPLATE (use this exact structure and commands):
{template}

BASE RESUME CONTENT (use this as the source of truth):
{base_resume}

EVIDENCE MAP (what matches this JD — use this to prioritise):
{evidence_summary}

ATS KEYWORDS TO WEAVE IN: {keywords_str}

PROJECT GITHUB URLS:
{project_urls}

TAILORING RULES:
1. Keep the EXACT LaTeX structure and custom commands
2. Rewrite summary to target this specific role
   Keep "Aspiring AI Engineer" framing
3. SELECT ONLY 2 PROJECTS maximum
   Choose the 2 most relevant to this JD
   based on the evidence map confidence scores
4. Weave JD keywords into bullets naturally
5. Keep ALL real metrics exactly as written
6. Do NOT invent new achievements
7. Every bullet must come from the base resume
8. Use exact GitHub URLs provided
9. Escape special LaTeX characters:
   & → \\&   % → \\%   $ → \\$
10. CRITICAL — ONE PAGE ONLY:
    Maximum 2 projects
    Maximum 3 bullets per experience role
    Maximum 3 bullets per project
    Keep summary under 3 lines
    If content is too long cut bullets not sections
11. Return ONLY valid LaTeX
    Start with \\documentclass
    End with \\end{{document}}
"""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=8096,
        messages=[{"role": "user", "content": prompt}],
    )

    content = response.content[0].text.strip()

    # Strip markdown fences if Claude wraps in ```latex
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("latex"):
            content = content[5:]
        content = content.strip()

    return content
