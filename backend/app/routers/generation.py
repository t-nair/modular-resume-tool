"""Flow B: Resume generation (template rendering + PDF compilation)."""

import re
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.resume import Bullet, Entity, Resume, Section, Skill
from app.services.pdf_compiler import CompilationError, compile_latex
from app.services.template_engine import render_resume

router = APIRouter()

# Packages the generated body relies on (itemize options, \href)
REQUIRED_PACKAGES = ["enumitem", "hyperref"]


class GenerateRequest(BaseModel):
    resume_id: uuid.UUID
    entity_ids: list[uuid.UUID]
    include_skills: bool = True
    header_info: dict | None = None


class GenerateResponse(BaseModel):
    tex_source: str


@router.post("/resumes/generate/tex", response_model=GenerateResponse)
async def generate_tex(req: GenerateRequest, db: AsyncSession = Depends(get_db)):
    """Generate tailored LaTeX source from selected entities."""
    tex_source = await _build_tex(db, req)
    return GenerateResponse(tex_source=tex_source)


@router.post("/resumes/generate/pdf")
async def generate_pdf(req: GenerateRequest, db: AsyncSession = Depends(get_db)):
    """Generate tailored PDF from selected entities."""
    tex_source = await _build_tex(db, req)

    try:
        pdf_bytes = await compile_latex(tex_source)
    except CompilationError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=resume.pdf"},
    )


async def _build_tex(db: AsyncSession, req: GenerateRequest) -> str:
    """Build LaTeX source from selected entities."""
    # Fetch selected entities with their bullets and section info
    result = await db.execute(
        select(Entity)
        .where(Entity.id.in_(req.entity_ids))
        .options(
            selectinload(Entity.bullets),
            selectinload(Entity.section),
        )
    )
    entities = result.scalars().all()

    if not entities:
        raise HTTPException(status_code=400, detail="No entities found for given IDs")

    # Group entities by section
    section_map: dict[str, dict] = {}
    for entity in entities:
        sec_name = entity.section.name
        if sec_name not in section_map:
            section_map[sec_name] = {
                "name": sec_name,
                "display_order": entity.section.display_order,
                "entities": [],
            }
        section_map[sec_name]["entities"].append({
            "title": entity.title,
            "subtitle": entity.subtitle,
            "date_range": entity.date_range,
            "location": entity.location,
            "bullets": [b.text for b in sorted(entity.bullets, key=lambda x: x.display_order)],
        })

    mutable_sections = [{"kind": "mutable", **sec} for sec in section_map.values()]

    # Fetch immutable sections
    result = await db.execute(
        select(Section)
        .where(Section.resume_id == req.resume_id, Section.is_mutable == False)  # noqa: E712
    )
    immutable = result.scalars().all()
    immutable_sections = [
        {"kind": "raw", "name": s.name, "display_order": s.display_order, "raw_latex": s.raw_latex}
        for s in immutable
        if s.raw_latex
    ]

    # Keep the original resume's section order
    ordered = sorted(mutable_sections + immutable_sections, key=lambda s: s["display_order"])

    # Fetch skills if requested; placed just before the first tailored section
    if req.include_skills:
        result = await db.execute(
            select(Skill).where(Skill.resume_id == req.resume_id)
        )
        skill_rows = result.scalars().all()
        if skill_rows:
            skills = {
                "kind": "skills",
                "items": [{"category": s.category, "items": s.items} for s in skill_rows],
            }
            first_mutable = next(
                (i for i, sec in enumerate(ordered) if sec["kind"] == "mutable"), len(ordered)
            )
            ordered.insert(first_mutable, skills)

    # Reuse the uploaded resume's preamble (custom macros, fonts, margins) and header
    resume = await db.get(Resume, req.resume_id)
    preamble, original_header = _split_original(resume.raw_tex if resume else "")

    return render_resume(
        sections=ordered,
        header_info=req.header_info,
        preamble=preamble,
        original_header=original_header,
    )


def _split_original(raw_tex: str) -> tuple[str | None, str | None]:
    """Extract the preamble and the pre-first-section header from the original .tex."""
    doc_start = raw_tex.find(r"\begin{document}")
    if doc_start == -1:
        return None, None

    preamble = raw_tex[:doc_start].rstrip()
    if r"\documentclass" not in preamble:
        return None, None
    for pkg in REQUIRED_PACKAGES:
        if not re.search(r"\\usepackage(\[[^\]]*\])?\{[^}]*\b" + pkg + r"\b", preamble):
            preamble += "\n\\usepackage{" + pkg + "}"

    body = raw_tex[doc_start + len(r"\begin{document}"):]
    first_section = re.search(r"\\section\*?\{", body)
    header = body[: first_section.start()] if first_section else ""
    header = header.strip() or None

    return preamble, header
