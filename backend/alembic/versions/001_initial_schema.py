"""Initial schema with pgvector

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Resumes
    op.create_table(
        "resumes",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("raw_tex", sa.Text, nullable=False),
        sa.Column("plain_text", sa.Text, nullable=True),
        sa.Column("page_limit", sa.Integer, default=1),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # Sections
    op.create_table(
        "sections",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("resume_id", sa.UUID(), sa.ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("display_order", sa.Integer, nullable=False),
        sa.Column("is_mutable", sa.Boolean, default=True),
        sa.Column("raw_latex", sa.Text, nullable=True),
    )

    # Entities
    op.create_table(
        "entities",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("section_id", sa.UUID(), sa.ForeignKey("sections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("subtitle", sa.String(255), nullable=True),
        sa.Column("date_range", sa.String(100), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("raw_latex", sa.Text, nullable=True),
    )

    # Bullets with vector embedding
    op.create_table(
        "bullets",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("entity_id", sa.UUID(), sa.ForeignKey("entities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("display_order", sa.Integer, nullable=False),
        sa.Column("embedding", Vector(384), nullable=True),
    )

    # HNSW index on bullet embeddings for fast cosine similarity
    op.execute(
        "CREATE INDEX ix_bullets_embedding ON bullets USING hnsw (embedding vector_cosine_ops)"
    )

    # Skills with GIN index
    op.create_table(
        "skills",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("resume_id", sa.UUID(), sa.ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("items", sa.ARRAY(sa.String), nullable=False),
    )
    op.execute("CREATE INDEX ix_skills_items ON skills USING GIN (items)")

    # Job Descriptions
    op.create_table(
        "job_descriptions",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("company", sa.String(255), nullable=True),
        sa.Column("raw_text", sa.Text, nullable=False),
        sa.Column("extracted_skills", sa.ARRAY(sa.String), nullable=True),
        sa.Column("extracted_requirements", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # Scoring Results
    op.create_table(
        "scoring_results",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("resume_id", sa.UUID(), sa.ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", sa.UUID(), sa.ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("overall_score", sa.Float, nullable=False),
        sa.Column("sub_scores", sa.JSON, nullable=False),
        sa.Column("cover_letter", sa.Text, nullable=True),
        sa.Column("improvement_ideas", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("scoring_results")
    op.drop_table("job_descriptions")
    op.drop_table("skills")
    op.execute("DROP INDEX IF EXISTS ix_bullets_embedding")
    op.drop_table("bullets")
    op.drop_table("entities")
    op.drop_table("sections")
    op.drop_table("resumes")
    op.execute("DROP EXTENSION IF EXISTS vector")
