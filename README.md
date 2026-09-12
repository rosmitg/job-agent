# Job Application Intelligence Agent

An agentic AI system that tailors job applications
using evidence from your real experience.

## Architecture
JD → Requirements Extraction
   → Evidence Retrieval (profile + GitHub)
   → Requirement/Evidence Matching
   → Tailored Resume Generation
   → Evaluation + Revision Loop
   → Human Approval
   → Export

## Stack
Python, Anthropic API, Pydantic, GitHub API

## Setup
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```
