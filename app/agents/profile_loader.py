# app/agents/profile_loader.py

import json
from app.models import CandidateProfile


def load_profile(path: str = "data/profile.json") -> CandidateProfile:
    """
    Reads candidate profile from JSON file.
    Returns validated CandidateProfile object.
    """
    with open(path) as f:
        data = json.load(f)
    return CandidateProfile(**data)
