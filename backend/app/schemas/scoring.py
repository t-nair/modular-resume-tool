import uuid
from datetime import datetime

from pydantic import BaseModel


class ScoringRequest(BaseModel):
    resume_id: uuid.UUID
    job_id: uuid.UUID
    resume_tex: str | None = None
    cover_letter: str | None = None


class SubScores(BaseModel):
    keyword_match: float
    experience_relevance: float
    skills_alignment: float
    presentation_quality: float


class ScoringResponse(BaseModel):
    id: uuid.UUID
    overall_score: float
    sub_scores: SubScores
    cover_letter: str | None = None
    improvement_ideas: list[str] = []
    created_at: datetime

    model_config = {"from_attributes": True}
