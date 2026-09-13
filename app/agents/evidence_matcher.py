# app/agents/evidence_matcher.py

import json
import anthropic
from app.models import (
    ParsedJD,
    CandidateProfile,
    EvidenceMatch,
    JobRequirementEvidenceMap,
    RequirementImportance,
)

client = anthropic.Anthropic()


def match_evidence(
    jd: ParsedJD, profile: CandidateProfile
) -> JobRequirementEvidenceMap:
    """
    For each JD requirement find evidence
    in the candidate profile.
    Returns full evidence map with confidence
    scores and gaps identified.
    """
    matches = []

    # Convert profile to string summary for Claude
    profile_summary = f"""
CANDIDATE: {profile.name}

SKILLS: {', '.join(profile.skills)}

EXPERIENCE:
{chr(10).join([
    f"- {exp.role} at {exp.company} ({exp.start_year}-{exp.end_year or 'present'}): {exp.description} | Skills: {', '.join(exp.skills)}"
    for exp in profile.experience
])}

PROJECTS:
{chr(10).join([
    f"- {proj.name}: {proj.description} | Stack: {', '.join(proj.stack)} | Metrics: {', '.join(proj.metrics)} | Highlights: {', '.join(proj.highlights)}"
    for proj in profile.projects
])}

EDUCATION:
{chr(10).join([
    f"- {edu.degree} in {edu.field} from {edu.institution} ({edu.graduation_year}) | {', '.join(edu.achievements)}"
    for edu in profile.education
])}
"""

    for requirement in jd.requirements:

        prompt = f"""
You are an expert recruiter matching a candidate profile against a job requirement.

JOB REQUIREMENT:
Text: {requirement.text}
Importance: {requirement.importance.value}
Category: {requirement.category}
Keywords: {', '.join(requirement.keywords)}

CANDIDATE PROFILE:
{profile_summary}

Find evidence in the candidate profile that supports this requirement.
Be honest — if no evidence exists say so clearly.

Return ONLY valid JSON, no markdown, no explanation:
{{
    "evidence": [
        "specific evidence found e.g. Python listed in skills",
        "used in Financial Doc Intelligence project"
    ],
    "confidence": 0.95,
    "gap": false,
    "gap_description": null
}}

confidence rules:
1.0 = strong direct evidence
0.7 = good evidence, not perfect match
0.4 = weak or indirect evidence
0.0 = no evidence found

gap rules:
false = some evidence exists (confidence > 0.3)
true = no meaningful evidence (confidence <= 0.3)

gap_description:
null if no gap
"reason why gap exists" if gap is true
"""

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        content = response.content[0].text.strip()

        # Strip markdown fences if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        data = json.loads(content)

        match = EvidenceMatch(
            requirement=requirement,
            evidence=data.get("evidence", []),
            confidence=data.get("confidence", 0.0),
            gap=data.get("gap", True),
            gap_description=data.get("gap_description"),
        )

        matches.append(match)

    return JobRequirementEvidenceMap(
        job_title=jd.job_title, company=jd.company_name, matches=matches
    )


def check_filter_gate(
    evidence_map: JobRequirementEvidenceMap,
) -> tuple[bool, list[str]]:
    """
    Check if candidate meets all must-have requirements.
    Returns (passed, list of failure reasons).
    """
    if not evidence_map.must_have_gaps:
        return True, []

    reasons = [
        f"Missing must-have: {m.requirement.text} — {m.gap_description or 'no evidence found'}"
        for m in evidence_map.must_have_gaps
    ]

    return False, reasons
