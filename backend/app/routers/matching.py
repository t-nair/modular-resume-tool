"""Flow B: Job description matching and entity search."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.job import JobDescription
from app.schemas.job import (
    EntitySearchRequest,
    ExtractedRequirements,
    JobMatchRequest,
    JobMatchResponse,
    RankedEntity,
)
from app.services.hybrid_search import hybrid_search, vector_search
from app.services.job_parser import extract_entities

router = APIRouter()


@router.post("/jobs/match", response_model=JobMatchResponse)
async def match_job(req: JobMatchRequest, db: AsyncSession = Depends(get_db)):
    """Parse a job description, extract entities, and run hybrid search."""
    # 1. Extract skills/requirements with GLiNER
    extracted = extract_entities(req.job_text)

    # 2. Store the job description
    job = JobDescription(
        title=req.title,
        company=req.company,
        raw_text=req.job_text,
        extracted_skills=extracted["all_skills"],
        extracted_requirements={
            "hard_skills": extracted["hard_skills"],
            "soft_skills": extracted["soft_skills"],
            "domain_keywords": extracted["domain_keywords"],
        },
    )
    db.add(job)
    await db.flush()

    # 3. Run hybrid search (BM25 filter + vector rerank + entity rollup)
    all_keywords = extracted["all_skills"] + extracted["domain_keywords"]
    ranked = await hybrid_search(
        db=db,
        resume_id=req.resume_id,
        keywords=all_keywords,
        job_text=req.job_text,
        top_k=20,
    )

    ranked_entities = [
        RankedEntity(
            entity_id=r["entity_id"],
            section_name=r["section_name"],
            title=r["title"],
            subtitle=r["subtitle"],
            score=r["score"],
            matching_bullets=r["matching_bullets"],
        )
        for r in ranked
    ]

    await db.commit()

    return JobMatchResponse(
        job_id=job.id,
        extracted_skills=extracted["all_skills"],
        extracted_requirements=ExtractedRequirements(
            hard_skills=extracted["hard_skills"],
            soft_skills=extracted["soft_skills"],
            domain_keywords=extracted["domain_keywords"],
        ),
        ranked_entities=ranked_entities,
    )


@router.post("/entities/search", response_model=list[RankedEntity])
async def search_entities(req: EntitySearchRequest, db: AsyncSession = Depends(get_db)):
    """Free-text vector search across resume entities."""
    results = await vector_search(
        db=db,
        resume_id=req.resume_id,
        query_text=req.query,
        top_k=req.top_k,
    )
    return [
        RankedEntity(
            entity_id=r["entity_id"],
            section_name=r["section_name"],
            title=r["title"],
            subtitle=r["subtitle"],
            score=r["score"],
            matching_bullets=r["matching_bullets"],
        )
        for r in results
    ]
