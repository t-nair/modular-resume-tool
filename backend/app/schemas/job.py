import uuid
from datetime import datetime

from pydantic import BaseModel


class JobMatchRequest(BaseModel):
    resume_id: uuid.UUID
    job_text: str
    title: str | None = None
    company: str | None = None


class ExtractedRequirements(BaseModel):
    hard_skills: list[str] = []
    soft_skills: list[str] = []
    domain_keywords: list[str] = []


class RankedEntity(BaseModel):
    entity_id: uuid.UUID
    section_name: str
    title: str
    subtitle: str | None = None
    score: float
    matching_bullets: list[str] = []


class JobMatchResponse(BaseModel):
    job_id: uuid.UUID
    extracted_skills: list[str]
    extracted_requirements: ExtractedRequirements
    ranked_entities: list[RankedEntity]


class JobDescriptionOut(BaseModel):
    id: uuid.UUID
    title: str | None = None
    company: str | None = None
    raw_text: str
    extracted_skills: list[str] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class EntitySearchRequest(BaseModel):
    resume_id: uuid.UUID
    query: str
    top_k: int = 10
