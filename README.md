# Job Application Intelligence Agent

An agentic AI system that tailors job applications using evidence from your real experience.

Paste a job description — the agent analyses requirements, matches your profile, generates a tailored LaTeX resume grounded in verified evidence, evaluates quality, and revises automatically if needed.

---

## Architecture

```text
JD Text
   ↓
parse_jd
Extract structured requirements and importance levels
   ↓
match_evidence
Match each requirement to candidate profile with confidence scores
   ↓
filter_gate
Stop if must-have requirements not met — no wasted generation
   ↓
generate_resume
Tailor LaTeX resume from evidence map only — no hallucination
   ↓
evaluate
Programmatic checks + LLM-as-judge rubric scoring
   ↓
revise (max 2x)
Targeted revision using failures and recommendation as feedback
   ↓
human_review
PDF compiled automatically — review before submitting
```

Built with LangGraph — stateful graph with conditional routing, revision loops, and human-in-the-loop approval.

---

## Why not just paste the JD into ChatGPT

- **Evidence-grounded generation** — every bullet traces back to verified evidence. Claude only writes from matched evidence, not imagination.
- **Filter gate** — must-have requirements checked before any generation. Stops immediately if you are disqualified.
- **Dual evaluation** — programmatic checks (keyword coverage, metrics preserved, seniority not embellished) combined with LLM-as-judge rubric scoring across honesty, relevance, specificity, clarity, and ATS friendliness.
- **Revision loop** — failures and LLM recommendations fed back as external feedback. Agent revises until quality gate passes or budget runs out.
- **LaTeX output** — generates and compiles a professional PDF using your existing template.

---

## Stack

| Component | Technology |
|-----------|-----------|
| Agent orchestration | LangGraph |
| LLM | Claude Haiku via Anthropic API |
| JD parsing | Claude + Pydantic |
| Evidence matching | Claude semantic matching |
| Resume generation | Claude + LaTeX template |
| Evaluation | Programmatic + LLM-as-judge |
| Output | pdflatex compiled PDF |

---

## Project Structure

```text
job-agent/
├── app/
│   ├── agents/
│   │   ├── jd_parser.py          # raw JD text → ParsedJD
│   │   ├── profile_loader.py     # profile.json → CandidateProfile
│   │   ├── evidence_matcher.py   # requirements → EvidenceMap
│   │   ├── resume_generator.py   # EvidenceMap → LaTeX resume
│   │   ├── evaluator.py          # programmatic + LLM-as-judge
│   │   └── revision_loop.py      # targeted revision from failures
│   ├── models.py                 # Pydantic data models
│   └── graph.py                  # LangGraph agent
├── data/
│   ├── profile.json              # your candidate profile
│   ├── base_resume.md            # your base resume content
│   └── template.tex              # your LaTeX resume template
├── .env.example
└── README.md
```

---

## Data Models

```text
ParsedJD
  → job_title, company, requirements (MUST_HAVE / PREFERRED / NICE_TO_HAVE)

CandidateProfile
  → experience, projects, education, skills

EvidenceMatch
  → one requirement mapped to evidence with confidence score and gap flag

JobRequirementEvidenceMap
  → all matches collected with coverage_score and must_have_coverage

TailoredResume
  → LaTeX output grounded in evidence map
```

---

## Setup

```bash
git clone https://github.com/rosmitg/job-agent.git
cd job-agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
sudo apt install texlive-latex-base texlive-fonts-recommended texlive-latex-extra
cp .env.example .env
```

Fill in `.env`:

```bash
ANTHROPIC_API_KEY=your_key_here
```

Add your profile:

```bash
# Edit data/profile.json with your experience, projects, skills
# Edit data/base_resume.md with your base resume content
# Edit data/template.tex with your LaTeX resume template
```

---

## Usage

```bash
python -m app.graph
```

Edit the JD text at the bottom of `app/graph.py` or import and call `run()`:

```python
from app.graph import run

run("""
AI Engineer at Westpac Sydney.
Must have Python and LangChain.
Must have Australian work rights.
Preferred: Docker, AWS.
Full time graduate role.
Build RAG systems for banking.
""")
```

Output: `output_resume.pdf` compiled and ready to review.

---

## Agent Flow

```text
node_parse_jd
   ↓ always
node_match_evidence
   ↓ always
node_filter_gate
   ↓ PASS → node_generate
   ↓ FAIL → END (log reasons, don't apply)
node_generate
   ↓ always
node_evaluate
   ↓ PASS → node_human_review
   ↓ FAIL + revisions < 2 → node_revise
   ↓ FAIL + revisions >= 2 → node_human_review
node_revise
   ↓ always → node_evaluate
node_human_review
   ↓ END
```

---

## Evaluation Criteria

Programmatic checks (Python — no LLM):

- Keyword coverage from JD requirements
- Real metrics preserved (0.955, 94%, 4.88/5)
- Seniority not embellished
- Graduation status correct
- Word count within range

LLM-as-judge rubric (1-5 each):

- Honesty — no inflated claims
- Relevance — experience matches role
- Specificity — bullets have real metrics
- Clarity — readable and well structured
- ATS friendliness — keywords woven in naturally

Quality gate thresholds:

- Keyword coverage above 60%
- Metrics coverage above 50%
- Honesty score above 3/5
- Total subjective score above 18/25

---

## Known Limitations

- Profile maintained manually in JSON — no automated ingestion yet
- GitHub API integration planned but not built
- Job board scraping not included — paste JD manually
- Telegram delivery planned for V2
- Cover letter generation planned for V2

---

## Learning Objectives

Built to own the following concepts end to end:

- Pydantic data models as contracts between agent components
- LangGraph stateful graph with conditional routing
- Evidence-grounded generation to prevent hallucination
- Dual evaluation — objective programmatic + subjective LLM-as-judge
- External feedback in revision loop
- Human-in-the-loop as a graph node
- LaTeX resume compilation from agent output
