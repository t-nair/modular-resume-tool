from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import editing, generation, ingestion, matching, scoring


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load models once at startup
    from app.services.job_parser import load_gliner_model
    from app.services.embedder import load_embedding_model
    load_gliner_model()
    load_embedding_model()
    yield


app = FastAPI(title="Modular Resume Tool", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingestion.router, prefix="/api", tags=["ingestion"])
app.include_router(editing.router, prefix="/api", tags=["editing"])
app.include_router(matching.router, prefix="/api", tags=["matching"])
app.include_router(generation.router, prefix="/api", tags=["generation"])
app.include_router(scoring.router, prefix="/api", tags=["scoring"])


@app.get("/api/health")
async def health():
    return {"status": "ok"}
