from pydantic import BaseModel, Field, field_validator
from enum import Enum


class Recommendation(str, Enum):
    STRONG_MATCH = "Strong Match"
    POTENTIAL_MATCH = "Potential Match"
    REJECT = "Reject"


class Resume(BaseModel):
    matching_keywords: list[str] = Field(
        default_factory=list,
        description="""
        "List technical skills AND concepts that appear in BOTH JD and Resume."
        """,
    )

    missing_keywords: list[str] = Field(
        default_factory=list,
        description=(
            "List key missing requirements. "
            "Logic: If JD says 'A or B' and candidate has A, list neither. "
            "Ignore nice-to-haves. If role mismatch, list the core missing domain "
            "(e.g., 'Backend Development')."
        ),
    )

    years_experience_required: int = Field(
        ge=0,
        description="Min years in JD. Extract lower bound (e.g., '3-5' -> 3). Default 0.",
    )

    years_experience_actual: int = Field(
        ge=0,
        description=(
            "Total professional years. IMPORTANT: Must be a WHOLE NUMBER (Integer). If 0.75, use 1 or 0."
        ),
    )

    recommendation: Recommendation = Field(
        description=(
            "Must be EXACTLY one of: 'Strong Match', 'Potential Match', or 'Reject'. Do not shorten."
            "FINAL VERDICT LOGIC (Apply in order):"
            "1. ROLE CHECK: If JD is 'Backend' and Candidate is 'Data Scientist' or 'Frontend', Verdict = REJECT (Fundamental Mismatch)."
            "2. PRIMARY TECH: If Candidate misses the core language (e.g., JD requires Java, Candidate has Python), Verdict = REJECT."
            "3. EXPERIENCE: If Candidate has < 50% of required years, Verdict = REJECT or POTENTIAL."
            "4. POTENTIAL MATCH: Role is correct, Core Tech is present, but missing cloud/tools (e.g., knows FastAPI but not AWS/Kafka)."
            "5. STRONG MATCH: Role is correct, Core Tech is perfect, and has most secondary tools."
        )
    )

    profile_summary: str = Field(
        description="""2-3 sentence executive decision logic. If Reject, explain why (e.g., Role Mismatch).
            Eg: 'Good Python skills, but rejected due to lack of required NLP experience.'
            """
    )

    @field_validator("matching_keywords", "missing_keywords", mode="before")
    @classmethod
    def handle_nulls(cls, v):
        if v is None:
            return []
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "recommendation": "Potential Match",
                "years_experience_required": 5,
                "years_experience_actual": 3,
                "matching_keywords": ["Python", "FastAPI", "SQL"],
                "missing_keywords": ["AWS", "Docker", "Kubernetes"],
                "profile_summary": "Candidate has strong backend coding skills matching the core requirements. However, they lack the required cloud infrastructure experience (AWS/Docker) needed for deployment tasks.",
            }
        }
    }


class AnalysisItem(BaseModel):
    filename: str
    analysis: Resume


class BatchAnalysisResponse(BaseModel):
    results: list[AnalysisItem]


class JobQuery(BaseModel):
    job_description: str
    session_id: str


class ChatQuery(BaseModel):
    resume_id: str
    question: str
    job_description: str | None = None


class ChatResponse(BaseModel):
    answer: str
