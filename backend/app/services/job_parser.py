"""GLiNER-based entity extraction from job descriptions."""

from gliner import GLiNER

_model: GLiNER | None = None

LABELS = [
    "programming language",
    "framework",
    "tool",
    "database",
    "cloud platform",
    "soft skill",
    "domain",
    "certification",
    "methodology",
    "technology",
]


def load_gliner_model():
    """Load GLiNER model into memory. Called once at startup."""
    global _model
    _model = GLiNER.from_pretrained("urchade/gliner_medium-v2.1")


def extract_entities(text: str) -> dict:
    """Extract skills and requirements from a job description."""
    if _model is None:
        raise RuntimeError("GLiNER model not loaded. Call load_gliner_model() first.")

    entities = _model.predict_entities(text, LABELS, threshold=0.4)

    # Deduplicate and group by label
    hard_skills = set()
    soft_skills = set()
    domain_keywords = set()
    all_skills = set()

    for ent in entities:
        text_val = ent["text"].strip()
        label = ent["label"]

        all_skills.add(text_val)

        if label in ("programming language", "framework", "tool", "database",
                      "cloud platform", "certification", "technology"):
            hard_skills.add(text_val)
        elif label == "soft skill":
            soft_skills.add(text_val)
        elif label in ("domain", "methodology"):
            domain_keywords.add(text_val)

    return {
        "all_skills": sorted(all_skills),
        "hard_skills": sorted(hard_skills),
        "soft_skills": sorted(soft_skills),
        "domain_keywords": sorted(domain_keywords),
    }
