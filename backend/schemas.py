from pydantic import BaseModel, Field, field_validator, computed_field
from enum import Enum


class Recommendation(str, Enum):
    STRONG_MATCH = "Strong Match"
    POTENTIAL_MATCH = "Potential Match"
    REJECT = "Reject"


class Resume(BaseModel):
    is_valid_job_description: bool = Field(
        description="Check if the Job Description text is valid. If it is nonsense (e.g., 'hello', 'test'), too short, or lacks technical requirements, set this to False. Otherwise, True."
    )
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
            "The total years of full-time professional employment. "
            "CRITICAL RULES: "
            "1. Only calculate duration from sections explicitly titled 'Experience', 'Work History', or 'Employment'. "
            "2. ABSOLUTELY DO NOT count time from the 'Projects', 'Academic Projects', or 'Education' sections. "
            "3. If the resume has no section titled 'Experience' or 'Employment', return 0. "
            "4. Do not infer years based on skill level. If no dates of employment are listed, the value must be 0."
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
        if not self.is_valid_job_description:
            return 0

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


class ChatQuery(BaseModel):
    resume_id: str
    question: str
    job_description: str | None = None


class ChatResponse(BaseModel):
    answer: str
