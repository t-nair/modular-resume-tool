"""Flow A: Resume upload, parsing, classification, embedding."""

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.resume import Bullet, Entity, Resume, Section, Skill
from app.schemas.resume import ResumeOut, ResumeUploadResponse, SkillOut
from app.services.classifier import classify_section
from app.services.embedder import embed_texts
from app.services.segmenter import segment_latex
from app.services.tex_extractor import extract_plain_text

router = APIRouter()


@router.post("/resumes/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    page_limit: int = Form(1),
    db: AsyncSession = Depends(get_db),
):
    """Upload a .tex resume file. Runs the full ingestion pipeline."""
    if not file.filename or not file.filename.endswith(".tex"):
        raise HTTPException(status_code=400, detail="Only .tex files are supported")

    raw_tex = (await file.read()).decode("utf-8")

    # 1. Extract plain text
    plain_text = await extract_plain_text(raw_tex)

    # 2. Create resume record
    resume = Resume(
        filename=file.filename,
        raw_tex=raw_tex,
        plain_text=plain_text,
        page_limit=page_limit,
    )
    db.add(resume)
    await db.flush()

    # 3. Segment the LaTeX
    segmented = segment_latex(raw_tex)

    total_entities = 0
    total_bullets = 0
    total_skills = 0
    all_bullet_objects: list[Bullet] = []
    all_bullet_texts: list[str] = []

    # 4. Classify each section and store
    for order, seg in enumerate(segmented):
        # Build text for classification from plain text or raw
        section_text = seg.raw_latex
        for entry in seg.entries:
            if entry.bullets:
                section_text += "\n" + "\n".join(entry.bullets)

        classified = await classify_section(seg.name, section_text)

        section = Section(
            resume_id=resume.id,
            name=seg.name,
            display_order=order,
            is_mutable=classified.get("is_mutable", True),
            raw_latex=seg.raw_latex if not classified.get("is_mutable", True) else None,
        )
        db.add(section)
        await db.flush()

        # Store entities
        for ent_data in classified.get("entities", []):
            entity = Entity(
                section_id=section.id,
                title=ent_data.get("title", "Untitled"),
                subtitle=ent_data.get("subtitle"),
                date_range=ent_data.get("date_range"),
                location=ent_data.get("location"),
                raw_latex=None,
            )
            db.add(entity)
            await db.flush()
            total_entities += 1

            # Store bullets
            for b_order, bullet_text in enumerate(ent_data.get("bullets", [])):
                bullet = Bullet(
                    entity_id=entity.id,
                    text=bullet_text,
                    display_order=b_order,
                )
                db.add(bullet)
                total_bullets += 1

                # Only embed mutable section bullets
                if classified.get("is_mutable", True):
                    all_bullet_objects.append(bullet)
                    all_bullet_texts.append(bullet_text)

        # Store skills
        for skill_data in classified.get("skills", []) or []:
            skill = Skill(
                resume_id=resume.id,
                category=skill_data.get("category", "General"),
                items=skill_data.get("items", []),
            )
            db.add(skill)
            total_skills += len(skill.items)

    await db.flush()

    # 5. Batch embed all mutable bullets
    if all_bullet_texts:
        embeddings = await embed_texts(all_bullet_texts)
        for bullet_obj, embedding in zip(all_bullet_objects, embeddings):
            bullet_obj.embedding = embedding

    await db.commit()

    return ResumeUploadResponse(
        id=resume.id,
        filename=resume.filename,
        sections_count=len(segmented),
        entities_count=total_entities,
        bullets_count=total_bullets,
        skills_count=total_skills,
    )


@router.get("/resumes/{resume_id}", response_model=ResumeOut)
async def get_resume(resume_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get a parsed resume with all sections, entities, and bullets."""
    result = await db.execute(
        select(Resume)
        .where(Resume.id == resume_id)
        .options(
            selectinload(Resume.sections)
            .selectinload(Section.entities)
            .selectinload(Entity.bullets)
        )
    )
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume


@router.get("/resumes/{resume_id}/skills", response_model=list[SkillOut])
async def get_skills(resume_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get all skills for a resume."""
    result = await db.execute(
        select(Skill).where(Skill.resume_id == resume_id)
    )
    return result.scalars().all()
