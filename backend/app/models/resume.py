import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename: Mapped[str] = mapped_column(String(255))
    raw_tex: Mapped[str] = mapped_column(Text)
    plain_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_limit: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    sections: Mapped[list["Section"]] = relationship(back_populates="resume", cascade="all, delete-orphan")


class Section(Base):
    __tablename__ = "sections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))
    display_order: Mapped[int] = mapped_column(Integer)
    is_mutable: Mapped[bool] = mapped_column(Boolean, default=True)
    raw_latex: Mapped[str | None] = mapped_column(Text, nullable=True)

    resume: Mapped["Resume"] = relationship(back_populates="sections")
    entities: Mapped[list["Entity"]] = relationship(back_populates="section", cascade="all, delete-orphan")


class Entity(Base):
    __tablename__ = "entities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    section_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sections.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255))
    subtitle: Mapped[str | None] = mapped_column(String(255), nullable=True)
    date_range: Mapped[str | None] = mapped_column(String(100), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_latex: Mapped[str | None] = mapped_column(Text, nullable=True)

    section: Mapped["Section"] = relationship(back_populates="entities")
    bullets: Mapped[list["Bullet"]] = relationship(back_populates="entity", cascade="all, delete-orphan")


class Bullet(Base):
    __tablename__ = "bullets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(Integer)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(384), nullable=True)

    entity: Mapped["Entity"] = relationship(back_populates="bullets")


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"))
    category: Mapped[str] = mapped_column(String(100))
    items: Mapped[list[str]] = mapped_column(ARRAY(String))
