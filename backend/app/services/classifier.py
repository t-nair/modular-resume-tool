"""GPT-4o-mini structured JSON classification of segmented resume chunks."""

import json
from openai import AsyncOpenAI

from app.config import settings

SYSTEM_PROMPT = """You are a resume parser. Given a segmented chunk of a resume, classify it into structured JSON.
You must ONLY classify and extract—never generate new text.

For each section, determine:
1. section_type: one of "experience", "education", "projects", "skills", "certifications", "summary", "other"
2. is_mutable: true for experience, projects, skills; false for education, certifications, summary
3. entities: list of sub-items (jobs, degrees, projects, etc.)

For each entity, extract:
- title: the main heading (job title, degree, project name)
- subtitle: secondary info (company name, university, etc.)
- date_range: date string if present
- location: location if present
- bullets: list of bullet point strings

For skills sections, extract:
- skills: list of {category: string, items: [string]} objects

Return valid JSON matching this schema:
{
  "section_type": string,
  "is_mutable": boolean,
  "entities": [
    {
      "title": string,
      "subtitle": string | null,
      "date_range": string | null,
      "location": string | null,
      "bullets": [string]
    }
  ],
  "skills": [
    {"category": string, "items": [string]}
  ] | null
}"""


async def classify_section(section_name: str, section_text: str) -> dict:
    """Send a segmented section to GPT-4o-mini for structured classification."""
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    user_content = f"Section name: {section_name}\n\nContent:\n{section_text}"

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        response_format={"type": "json_object"},
        temperature=0.0,
        max_tokens=4096,
    )

    raw = response.choices[0].message.content
    return json.loads(raw)


async def classify_sections(sections: list[dict]) -> list[dict]:
    """Classify multiple sections, returning structured data for each."""
    import asyncio

    tasks = [
        classify_section(s["name"], s["text"])
        for s in sections
    ]
    return await asyncio.gather(*tasks)
