from pydantic import BaseModel, Field, field_validator, computed_field
from enum import Enum


class Recommendation(str, Enum):
    STRONG_MATCH = "Strong Match"
    POTENTIAL_MATCH = "Potential Match"
    REJECT = "Reject"


class Resume(BaseModel):
    matching_keywords: list[str] = Field(
        default_factory=list,
        description="Key skills from Job Description that the candidate definitely has in resume",
    )

    missing_keywords: list[str] = Field(
        default_factory=list,
        description="Critical skills (must-haves) from Job Description that are missing in resume",
    )

    years_experience_required: int = Field(
        ge=0,
        description="The minimum years of experience mentioned in the Job Description, If not mentioned, use 0.",
    )

    years_experience_actual: int = Field(
        ge=0,
        description=(
            "The total years of work experience that is DIRECTLY RELEVANT to the Job Description. "
            "1. Compare every role in the Resume against the skills in the Job Description. "
            "2. If a role (e.g., 'Sales Associate') is unrelated to the target job (e.g., 'Python Engineer'), DO NOT count its duration. "
            "3. Strictly exclude student clubs, university leadership roles, and unpaid volunteering. "
            "4. Count relevant Internships as valid experience."
        ),
    )

    recommendation: Recommendation = Field(
        description="The Final verdict on the candidate"
    )

    profile_summary: str = Field(
        description="A 2-3 sentence executive summary. Don't simply list experience; explain the decision. Example: 'Good Python skills, but rejected due to lack of required NLP experience.'"
    )

    @field_validator("matching_keywords", "missing_keywords", mode="before")
    @classmethod
    def handle_nulls(cls, v):
        if v is None:
            return []
        return v

    @computed_field
    @property
    def match_score(self) -> int:
        score = 100

        score -= len(self.missing_keywords) * 5

        if self.years_experience_actual < self.years_experience_required:
            diff = self.years_experience_required - self.years_experience_actual

            penalty = min(30, diff * 10)
            score -= int(penalty)

        return max(0, score)

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
