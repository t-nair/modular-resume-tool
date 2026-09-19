"""Flow C: Resume scoring and evaluation."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.job import JobDescription
from app.models.resume import Resume
from app.models.scoring import ScoringResult
from app.schemas.scoring import ScoringRequest, ScoringResponse, SubScores
from app.services.scorer import evaluate_resume

router = APIRouter()


@router.post("/scoring/evaluate", response_model=ScoringResponse)
async def score_resume(req: ScoringRequest, db: AsyncSession = Depends(get_db)):
    """Evaluate a resume against a job description using GPT-4o."""
    # Fetch resume
    result = await db.execute(select(Resume).where(Resume.id == req.resume_id))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    # Fetch job description
    result = await db.execute(select(JobDescription).where(JobDescription.id == req.job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job description not found")

    # Use provided tex or fall back to stored plain text
    resume_text = req.resume_tex or resume.plain_text or resume.raw_tex

    # Run GPT-4o evaluation
    evaluation = await evaluate_resume(
        resume_text=resume_text,
        job_text=job.raw_text,
        cover_letter=req.cover_letter,
    )

    # Store result
    scoring = ScoringResult(
        resume_id=req.resume_id,
        job_id=req.job_id,
        overall_score=evaluation["overall_score"],
        sub_scores=evaluation["sub_scores"],
        cover_letter=evaluation.get("cover_letter"),
        improvement_ideas=evaluation.get("improvement_ideas"),
    )
    db.add(scoring)
    await db.commit()
    await db.refresh(scoring)

    return ScoringResponse(
        id=scoring.id,
        overall_score=scoring.overall_score,
        sub_scores=SubScores(**scoring.sub_scores),
        cover_letter=scoring.cover_letter,
        improvement_ideas=scoring.improvement_ideas or [],
        created_at=scoring.created_at,
    )
