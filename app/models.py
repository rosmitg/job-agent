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
