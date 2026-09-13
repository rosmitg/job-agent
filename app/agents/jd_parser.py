# app/agents/jd_parser.py

import json
import anthropic
from app.models import ParsedJD

client = anthropic.Anthropic()


def parse_jd(raw_text: str) -> ParsedJD:
    """
    Takes raw JD text.
    Calls Claude to extract structured information.
    Returns a validated ParsedJD object.
    """
    prompt = f"""
You are an expert job description analyser.
Extract structured information from the job description below.

Return ONLY a valid JSON object — no explanation, no markdown, no extra text.

Job Description:
{raw_text}

Return this exact JSON structure:
{{
    "id": "generate a short unique slug e.g. westpac-ai-engineer-2026",
    "job_title": "exact job title",
    "company_name": "company name",
    "location": "location",
    "domain": "industry domain e.g. fintech, crypto, healthcare, AI",
    "seniority": "graduate | junior | mid | senior",
    "employment_type": "full_time | part_time | contract | internship",
    "salary_range": "salary range if mentioned or null",
    "company_description": "brief description of what the company does",
    "requirements": [
        {{
            "id": "req_1",
            "text": "the requirement text",
            "importance": "must_have | preferred | nice_to_have",
            "category": "technical | experience | visa | soft_skill",
            "keywords": ["keyword1", "keyword2"]
        }}
    ],
    "responsibilities": [
        "responsibility 1",
        "responsibility 2"
    ]
}}
"""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    content = response.content[0].text.strip()

    # Strip markdown fences if Claude adds them
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()

    data = json.loads(content)
    return ParsedJD(**data)
