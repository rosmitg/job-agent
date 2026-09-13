from pydantic import BaseModel
from typing import Optional
from enum import Enum


class RequirementImportance(str, Enum):
    """
    How important is this requirement.
    MUST_HAVE = dealbreaker, filter gate
    PREFERRED = strengthens application if present
    NICE_TO_HAVE = bonus, barely matters if missing
    """

    MUST_HAVE = "must_have"
    PREFERRED = "preferred"
    NICE_TO_HAVE = "nice_to_have"


class JobRequirement(BaseModel):
    """
    A single requirement extracted from the JD.
    """

    id: str  # e.g. "req_1", "req_2"
    text: str  # the actual requirement text
    importance: RequirementImportance
    category: str  # "technical", "experience", "visa"
    keywords: list[str] = []  # ["Python", "PostgreSQL"]


class ParsedJD(BaseModel):
    """
    A parsed job description.
    """

    id: str
    job_title: str
    company_name: str
    location: str
    domain: Optional[str]
    seniority: str
    employment_type: str
    salary_range: Optional[str]
    company_description: Optional[str]
    requirements: list[JobRequirement] = []
    responsibilities: list[str] = []


# Add these to app/models.py


class Experience(BaseModel):
    company: str
    role: str
    start_year: int
    end_year: Optional[int] = None
    current: bool = False
    description: str
    skills: list[str] = []
    achievements: list[str] = []


class Project(BaseModel):
    name: str
    description: str
    stack: list[str] = []
    metrics: list[str] = []
    github_url: Optional[str] = None
    live_url: Optional[str] = None
    highlights: list[str] = []


class Education(BaseModel):
    institution: str
    degree: str
    field: str
    graduation_year: int
    achievements: list[str] = []


class CandidateProfile(BaseModel):
    name: str
    email: str
    phone: str
    location: str
    github_username: str
    portfolio_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    summary: str
    experience: list[Experience] = []
    projects: list[Project] = []
    education: list[Education] = []
    skills: list[str] = []


class EvidenceMatch(BaseModel):
    """
    One requirement matched to candidate evidence.
    One row in the evidence table.
    """

    requirement: JobRequirement
    evidence: list[str] = []  # what specifically supports this
    confidence: float = 0.0  # 0.0 to 1.0
    gap: bool = False  # True if no evidence found
    gap_description: Optional[str] = None  # why is there a gap


class JobRequirementEvidenceMap(BaseModel):
    """
    Full map of all JD requirements to candidate evidence.
    The whole table. Agent reads this to make decisions.
    """

    job_title: str
    company: str
    matches: list[EvidenceMatch] = []

    @property
    def coverage_score(self) -> float:
        """Percentage of requirements with evidence."""
        if not self.matches:
            return 0.0
        covered = sum(1 for m in self.matches if not m.gap)
        return covered / len(self.matches)

    @property
    def must_have_coverage(self) -> float:
        """Coverage of must-have requirements only."""
        must_haves = [
            m
            for m in self.matches
            if m.requirement.importance == RequirementImportance.MUST_HAVE
        ]
        if not must_haves:
            return 1.0
        covered = sum(1 for m in must_haves if not m.gap)
        return covered / len(must_haves)

    @property
    def gaps(self) -> list[EvidenceMatch]:
        """All requirements with no evidence."""
        return [m for m in self.matches if m.gap]

    @property
    def must_have_gaps(self) -> list[EvidenceMatch]:
        """Must-have requirements with no evidence — dealbreakers."""
        return [
            m
            for m in self.matches
            if m.gap and m.requirement.importance == RequirementImportance.MUST_HAVE
        ]
