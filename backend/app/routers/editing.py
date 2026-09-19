"""Editing a parsed resume after upload: add/edit/delete entries, import experience, manage sections."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.resume import Bullet, Entity, Resume, Section, Skill
from app.schemas.resume import (
    EntityCreate,
    EntityOut,
    EntityUpdate,
    ImportRequest,
    ImportResponse,
    SectionCreate,
    SectionOut,
)
from app.services.classifier import classify_section
from app.services.embedder import embed_texts
from app.services.segmenter import segment_latex

router = APIRouter()

# Imported text with no \section headers lands here unless a target section is given
DEFAULT_IMPORT_SECTION = "Experience"


@router.post("/resumes/{resume_id}/sections", response_model=SectionOut)
async def create_section(
    resume_id: uuid.UUID, req: SectionCreate, db: AsyncSession = Depends(get_db)
):
    """Add a new (mutable) section at the end of the resume."""
    await _get_resume(db, resume_id)
    section = await _create_section(db, resume_id, req.name.strip())
    await db.commit()
    return SectionOut(
        id=section.id,
        name=section.name,
        display_order=section.display_order,
        is_mutable=section.is_mutable,
        entities=[],
    )


@router.post("/resumes/{resume_id}/entities", response_model=EntityOut)
async def create_entity(
    resume_id: uuid.UUID, req: EntityCreate, db: AsyncSession = Depends(get_db)
):
    """Manually add an entity (job, project, ...) with bullets to a section."""
    section = await db.get(Section, req.section_id)
    if not section or section.resume_id != resume_id:
        raise HTTPException(status_code=404, detail="Section not found")

    entity = await _add_entities(db, section, [req.model_dump()])
    await db.commit()
    return await _load_entity(db, entity[0].id)


@router.post("/resumes/{resume_id}/import", response_model=ImportResponse)
async def import_experience(
    resume_id: uuid.UUID, req: ImportRequest, db: AsyncSession = Depends(get_db)
):
    """Parse pasted text or LaTeX into entities and add them to the resume.

    With section_id, everything goes into that section. Otherwise LaTeX \\section
    headers are used to route content into matching (or new) sections.
    """
    await _get_resume(db, resume_id)
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Nothing to import")

    if req.section_id:
        target = await db.get(Section, req.section_id)
        if not target or target.resume_id != resume_id:
            raise HTTPException(status_code=404, detail="Section not found")
        chunks = [(target.name, text, target)]
    else:
        segmented = segment_latex(text) if "\\section" in text else []
        if segmented:
            chunks = [(seg.name, seg.raw_latex, None) for seg in segmented]
        else:
            chunks = [(DEFAULT_IMPORT_SECTION, text, None)]

    created: list[Entity] = []
    skills_added = 0
    for name, chunk, section in chunks:
        classified = await classify_section(name, chunk)
        entities = classified.get("entities") or []

        if entities:
            if section is None:
                section = await _find_or_create_section(db, resume_id, name)
            created += await _add_entities(db, section, entities)

        skills_added += await _merge_skills(db, resume_id, classified.get("skills") or [])

    await db.commit()

    return ImportResponse(
        entities=[await _load_entity(db, e.id) for e in created],
        skills_added=skills_added,
    )


@router.delete("/entities/{entity_id}", status_code=204)
async def delete_entity(entity_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Delete an entity and its bullets."""
    result = await db.execute(delete(Entity).where(Entity.id == entity_id))
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Entity not found")
    await db.commit()


@router.put("/entities/{entity_id}", response_model=EntityOut)
async def update_entity(
    entity_id: uuid.UUID, req: EntityUpdate, db: AsyncSession = Depends(get_db)
):
    """Replace an entity's fields and bullets."""
    result = await db.execute(
        select(Entity)
        .where(Entity.id == entity_id)
        .options(selectinload(Entity.bullets), selectinload(Entity.section))
    )
    entity = result.scalar_one_or_none()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    entity.title = req.title.strip() or "Untitled"
    entity.subtitle = (req.subtitle or "").strip() or None
    entity.date_range = (req.date_range or "").strip() or None
    entity.location = (req.location or "").strip() or None

    # Reuse embeddings for bullets whose text is unchanged; embed only new/edited ones
    old_embeddings = {b.text: b.embedding for b in entity.bullets if b.embedding is not None}
    await db.execute(delete(Bullet).where(Bullet.entity_id == entity.id))

    texts = [b.strip() for b in req.bullets if b and b.strip()]
    new_bullets = [
        Bullet(entity_id=entity.id, text=text, display_order=order, embedding=old_embeddings.get(text))
        for order, text in enumerate(texts)
    ]
    db.add_all(new_bullets)

    if entity.section.is_mutable:
        to_embed = [b for b in new_bullets if b.embedding is None]
        if to_embed:
            embeddings = await embed_texts([b.text for b in to_embed])
            for bullet, embedding in zip(to_embed, embeddings):
                bullet.embedding = embedding

    await db.commit()
    return await _load_entity(db, entity.id)


@router.delete("/sections/{section_id}", status_code=204)
async def delete_section(section_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Delete a section with all its entities and bullets."""
    result = await db.execute(delete(Section).where(Section.id == section_id))
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Section not found")
    await db.commit()


async def _get_resume(db: AsyncSession, resume_id: uuid.UUID) -> Resume:
    resume = await db.get(Resume, resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume


async def _create_section(db: AsyncSession, resume_id: uuid.UUID, name: str) -> Section:
    max_order = await db.scalar(
        select(func.max(Section.display_order)).where(Section.resume_id == resume_id)
    )
    section = Section(
        resume_id=resume_id,
        name=name,
        display_order=(max_order if max_order is not None else -1) + 1,
        is_mutable=True,
    )
    db.add(section)
    await db.flush()
    return section


async def _find_or_create_section(db: AsyncSession, resume_id: uuid.UUID, name: str) -> Section:
    """Match an existing section by name (case-insensitive), else create one."""
    result = await db.execute(
        select(Section).where(
            Section.resume_id == resume_id,
            func.lower(Section.name) == name.strip().lower(),
        )
    )
    return result.scalars().first() or await _create_section(db, resume_id, name.strip())


async def _add_entities(db: AsyncSession, section: Section, entities: list[dict]) -> list[Entity]:
    """Store entities + bullets; embed bullets of mutable sections for matching."""
    created = []
    new_bullets: list[Bullet] = []
    for data in entities:
        entity = Entity(
            section_id=section.id,
            title=(data.get("title") or "Untitled").strip(),
            subtitle=data.get("subtitle") or None,
            date_range=data.get("date_range") or None,
            location=data.get("location") or None,
        )
        db.add(entity)
        await db.flush()
        created.append(entity)

        bullets = [b.strip() for b in data.get("bullets") or [] if b and b.strip()]
        for order, text in enumerate(bullets):
            bullet = Bullet(entity_id=entity.id, text=text, display_order=order)
            db.add(bullet)
            new_bullets.append(bullet)

    if section.is_mutable and new_bullets:
        embeddings = await embed_texts([b.text for b in new_bullets])
        for bullet, embedding in zip(new_bullets, embeddings):
            bullet.embedding = embedding

    await db.flush()
    return created


async def _merge_skills(db: AsyncSession, resume_id: uuid.UUID, skills: list[dict]) -> int:
    """Add imported skills, merging into existing categories without duplicates."""
    result = await db.execute(select(Skill).where(Skill.resume_id == resume_id))
    by_category = {s.category.lower(): s for s in result.scalars().all()}

    added = 0
    for data in skills:
        category = (data.get("category") or "General").strip()
        items = [i.strip() for i in data.get("items") or [] if i and i.strip()]
        existing = by_category.get(category.lower())
        if existing:
            known = {i.lower() for i in existing.items}
            new_items = [i for i in items if i.lower() not in known]
            if new_items:
                existing.items = existing.items + new_items
                added += len(new_items)
        elif items:
            skill = Skill(resume_id=resume_id, category=category, items=items)
            db.add(skill)
            by_category[category.lower()] = skill
            added += len(items)
    return added


async def _load_entity(db: AsyncSession, entity_id: uuid.UUID) -> Entity:
    result = await db.execute(
        select(Entity)
        .where(Entity.id == entity_id)
        .options(selectinload(Entity.bullets))
        .execution_options(populate_existing=True)
    )
    return result.scalar_one()
