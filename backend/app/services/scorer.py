"""GPT-4o scoring evaluation with rubric prompt and structured JSON output."""

import json
from openai import AsyncOpenAI

from app.config import settings

SCORING_PROMPT = """You are an expert resume reviewer and hiring consultant. Evaluate the following resume against the job description using this strict rubric.

Score each dimension from 0.0 to 1.0:

1. **keyword_match** (0-1): What percentage of hard skills, tools, and technologies from the JD appear in the resume? Exact matches count. Close synonyms get partial credit.

2. **experience_relevance** (0-1): How well do the candidate's work experiences, projects, and accomplishments align with the role's core responsibilities?

3. **skills_alignment** (0-1): Beyond keywords, does the depth and breadth of the candidate's skill set match what's needed? Consider years of experience signals and skill combinations.

4. **presentation_quality** (0-1): Is the resume well-organized, concise, and optimized for ATS parsing? Are bullet points impact-driven (metrics, outcomes)?

Then calculate:
- **overall_score**: Weighted average: keyword_match(0.3) + experience_relevance(0.35) + skills_alignment(0.2) + presentation_quality(0.15)
- Convert to a "% likelihood of getting a response" (0-100).

Also provide:
- **cover_letter**: A tailored cover letter draft (3-4 paragraphs) that bridges resume gaps and emphasizes alignment.
- **improvement_ideas**: 3-5 actionable suggestions to improve the resume for this specific role.

Return JSON matching this schema:
{
  "overall_score": float (0-100),
  "sub_scores": {
    "keyword_match": float (0-1),
    "experience_relevance": float (0-1),
    "skills_alignment": float (0-1),
    "presentation_quality": float (0-1)
  },
  "cover_letter": string,
  "improvement_ideas": [string]
}"""


async def evaluate_resume(
    resume_text: str,
    job_text: str,
    cover_letter: str | None = None,
) -> dict:
    """Run GPT-4o evaluation of resume against job description."""
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    user_content = f"""## Resume
{resume_text}

## Job Description
{job_text}"""

    if cover_letter:
        user_content += f"\n\n## Existing Cover Letter\n{cover_letter}"

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SCORING_PROMPT},
            {"role": "user", "content": user_content},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
        max_tokens=4096,
    )

    raw = response.choices[0].message.content
    return json.loads(raw)
