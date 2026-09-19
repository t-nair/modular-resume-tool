import uuid
from datetime import datetime

from pydantic import BaseModel


class BulletOut(BaseModel):
    id: uuid.UUID
    text: str
    display_order: int

    model_config = {"from_attributes": True}


class EntityOut(BaseModel):
    id: uuid.UUID
    title: str
    subtitle: str | None = None
    date_range: str | None = None
    location: str | None = None
    bullets: list[BulletOut] = []

    model_config = {"from_attributes": True}


class SectionOut(BaseModel):
    id: uuid.UUID
    name: str
    display_order: int
    is_mutable: bool
    entities: list[EntityOut] = []

    model_config = {"from_attributes": True}


class SkillOut(BaseModel):
    id: uuid.UUID
    category: str
    items: list[str]

    model_config = {"from_attributes": True}


class ResumeOut(BaseModel):
    id: uuid.UUID
    filename: str
    page_limit: int
    created_at: datetime
    sections: list[SectionOut] = []

    model_config = {"from_attributes": True}


class ResumeUploadResponse(BaseModel):
    id: uuid.UUID
    filename: str
    sections_count: int
    entities_count: int
    bullets_count: int
    skills_count: int


class SectionCreate(BaseModel):
    name: str


class EntityCreate(BaseModel):
    section_id: uuid.UUID
    title: str
    subtitle: str | None = None
    date_range: str | None = None
    location: str | None = None
    bullets: list[str] = []


class ImportRequest(BaseModel):
    text: str
    section_id: uuid.UUID | None = None


class ImportResponse(BaseModel):
    entities: list[EntityOut]
    skills_added: int


class EntityUpdate(BaseModel):
    title: str
    subtitle: str | None = None
    date_range: str | None = None
    location: str | None = None
    bullets: list[str] = []
