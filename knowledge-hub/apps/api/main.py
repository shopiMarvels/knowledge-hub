from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from redis import Redis
from rq import Queue
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os, pathlib, uuid

from packages.db.models import Base
from packages.db.models import Document, Chunk  # (we'll add these in step 4)

APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@db:5432/knowledge_hub")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
STORAGE_DIR = os.getenv("STORAGE_DIR", "/data")

app = FastAPI(title="MCP Knowledge Hub API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"] ,
    allow_headers=["*"],
)

# DB session
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Queue
redis = Redis.from_url(REDIS_URL)
q = Queue("default", connection=redis)

class Health(BaseModel):
    status: str
    version: str

@app.get("/healthz", response_model=Health)
async def healthz():
    return {"status": "ok", "version": APP_VERSION}

@app.get("/version")
async def version():
    return {"version": APP_VERSION}

@app.post("/documents")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(400, "Missing filename")
    ext = pathlib.Path(file.filename).suffix.lower()
    if ext not in [".pdf", ".docx", ".txt"]:
        raise HTTPException(415, "Only .pdf, .docx, .txt supported")

    # Persist metadata
    session = SessionLocal()
    try:
        doc = Document(filename=file.filename, mime=file.content_type or "application/octet-stream", status="uploaded")
        session.add(doc)
        session.commit()
        session.refresh(doc)
        # Save file under /data/uploads/{doc_id}/filename
        doc_dir = pathlib.Path(STORAGE_DIR) / "uploads" / str(doc.id)
        doc_dir.mkdir(parents=True, exist_ok=True)
        dst = doc_dir / file.filename
        with open(dst, "wb") as f:
            f.write(await file.read())
        # queue job
        q.enqueue("jobs.parse_document.run", document_id=doc.id, path=str(dst), storage_dir=STORAGE_DIR)
        return {"status": "queued", "document_id": doc.id}
    finally:
        session.close()

@app.get("/documents/{doc_id}")
async def get_document(doc_id: int):
    session = SessionLocal()
    try:
        doc = session.query(Document).get(doc_id)
        if not doc:
            raise HTTPException(404, "Not found")
        # count chunks
        chunk_count = session.query(Chunk).filter(Chunk.document_id == doc_id).count()
        return {"id": doc.id, "filename": doc.filename, "status": doc.status, "chunks": chunk_count}
    finally:
        session.close()
