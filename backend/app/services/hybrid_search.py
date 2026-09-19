"""Hybrid search: BM25 keyword filter + vector cosine rerank + entity rollup.

Implemented as a single SQL CTE query for efficiency.
"""

import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.embedder import embed_single

# Score bonus for bullets that literally contain an extracted keyword
KEYWORD_BOOST = 0.1


async def hybrid_search(
    db: AsyncSession,
    resume_id: uuid.UUID,
    keywords: list[str],
    job_text: str,
    top_k: int = 10,
) -> list[dict]:
    """
    1. Keyword match on bullet text (a score boost, not a hard filter, so
       bullets that are semantically relevant but worded differently still rank)
    2. Vector cosine similarity against embedded job description
    3. Rollup scores to entity level (avg of top bullet scores)
    """

    # Embed the full job description for vector reranking
    job_embedding = await embed_single(job_text)

    # Keyword match (OR on any keyword in bullet text)
    keyword_conditions = " OR ".join(
        [f"b.text ILIKE '%' || :kw_{i} || '%'" for i in range(len(keywords))]
    ) or "false"
    keyword_params = {f"kw_{i}": kw for i, kw in enumerate(keywords)}

    query = text(f"""
        WITH keyword_flagged AS (
            -- Step 1: Flag bullets that mention any extracted keyword
            SELECT b.id AS bullet_id,
                   b.entity_id,
                   b.text AS bullet_text,
                   b.embedding,
                   CASE WHEN ({keyword_conditions}) THEN 1 ELSE 0 END AS keyword_hit
            FROM bullets b
            JOIN entities e ON b.entity_id = e.id
            JOIN sections s ON e.section_id = s.id
            WHERE s.resume_id = :resume_id
              AND s.is_mutable = true
              AND b.embedding IS NOT NULL
        ),
        vector_scored AS (
            -- Step 2: Vector cosine similarity, boosted for keyword hits
            SELECT kf.bullet_id,
                   kf.entity_id,
                   kf.bullet_text,
                   1 - (kf.embedding <=> CAST(:job_embedding AS vector))
                     + :keyword_boost * kf.keyword_hit AS cosine_score
            FROM keyword_flagged kf
        ),
        entity_rollup AS (
            -- Step 3: Entity-level rollup (avg of top-3 bullet scores)
            SELECT vs.entity_id,
                   AVG(vs.cosine_score) AS avg_score,
                   array_agg(vs.bullet_text ORDER BY vs.cosine_score DESC) AS top_bullets
            FROM (
                SELECT *,
                       ROW_NUMBER() OVER (PARTITION BY entity_id ORDER BY cosine_score DESC) AS rn
                FROM vector_scored
            ) vs
            WHERE vs.rn <= 3
            GROUP BY vs.entity_id
        )
        SELECT er.entity_id,
               er.avg_score,
               er.top_bullets,
               e.title,
               e.subtitle,
               s.name AS section_name
        FROM entity_rollup er
        JOIN entities e ON er.entity_id = e.id
        JOIN sections s ON e.section_id = s.id
        ORDER BY er.avg_score DESC
        LIMIT :top_k
    """)

    params = {
        "resume_id": str(resume_id),
        "job_embedding": str(job_embedding),
        "top_k": top_k,
        "keyword_boost": KEYWORD_BOOST,
        **keyword_params,
    }

    result = await db.execute(query, params)
    rows = result.fetchall()

    return [
        {
            "entity_id": row.entity_id,
            "score": float(row.avg_score),
            "matching_bullets": list(row.top_bullets) if row.top_bullets else [],
            "title": row.title,
            "subtitle": row.subtitle,
            "section_name": row.section_name,
        }
        for row in rows
    ]


async def vector_search(
    db: AsyncSession,
    resume_id: uuid.UUID,
    query_text: str,
    top_k: int = 10,
) -> list[dict]:
    """Pure vector similarity search (no keyword filter)."""
    query_embedding = await embed_single(query_text)

    query = text("""
        SELECT e.id AS entity_id,
               e.title,
               e.subtitle,
               s.name AS section_name,
               AVG(1 - (b.embedding <=> CAST(:query_embedding AS vector))) AS avg_score,
               array_agg(b.text ORDER BY (1 - (b.embedding <=> CAST(:query_embedding AS vector))) DESC) AS top_bullets
        FROM bullets b
        JOIN entities e ON b.entity_id = e.id
        JOIN sections s ON e.section_id = s.id
        WHERE s.resume_id = :resume_id
          AND s.is_mutable = true
          AND b.embedding IS NOT NULL
        GROUP BY e.id, e.title, e.subtitle, s.name
        ORDER BY avg_score DESC
        LIMIT :top_k
    """)

    result = await db.execute(query, {
        "resume_id": str(resume_id),
        "query_embedding": str(query_embedding),
        "top_k": top_k,
    })
    rows = result.fetchall()

    return [
        {
            "entity_id": row.entity_id,
            "score": float(row.avg_score),
            "matching_bullets": list(row.top_bullets)[:3] if row.top_bullets else [],
            "title": row.title,
            "subtitle": row.subtitle,
            "section_name": row.section_name,
        }
        for row in rows
    ]
