"""Local sentence-transformers embedding service (all-MiniLM-L6-v2, 384-dim)."""

from sentence_transformers import SentenceTransformer

_model: SentenceTransformer | None = None

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384


def load_embedding_model():
    """Load the embedding model into memory. Called once at startup."""
    global _model
    _model = SentenceTransformer(MODEL_NAME)


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts, returning 384-dim vectors."""
    if not texts:
        return []
    if _model is None:
        raise RuntimeError("Embedding model not loaded. Call load_embedding_model() first.")

    embeddings = _model.encode(texts, normalize_embeddings=True)
    return [e.tolist() for e in embeddings]


async def embed_single(text: str) -> list[float]:
    """Embed a single text string."""
    result = await embed_texts([text])
    return result[0]
