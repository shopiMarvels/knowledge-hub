from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from redis import Redis
from rq import Queue
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import List, Optional
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

class SearchRequest(BaseModel):
    query: str
    k: int = 5

class ChunkResult(BaseModel):
    id: int
    text: str
    chunk_index: int
    document_id: int
    filename: str
    similarity_score: float

class SearchResponse(BaseModel):
    query: str
    results: List[ChunkResult]
    total_results: int

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

@app.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """Semantic search through document chunks using FAISS"""
    try:
        # Import the search function from the embedding job
        from packages.agents.jobs.embed_chunks import search_similar_chunks
        
        # Get similar chunk IDs and scores
        similar_chunks = search_similar_chunks(request.query, request.k)
        
        if not similar_chunks:
            return SearchResponse(
                query=request.query,
                results=[],
                total_results=0
            )
        
        # Get chunk details from database
        session = SessionLocal()
        try:
            chunk_ids = [chunk_id for chunk_id, _ in similar_chunks]
            chunks = session.query(Chunk, Document).join(
                Document, Chunk.document_id == Document.id
            ).filter(Chunk.id.in_(chunk_ids)).all()
            
            # Create results with similarity scores
            chunk_data = {chunk.id: (chunk, doc) for chunk, doc in chunks}
            results = []
            
            for chunk_id, similarity_score in similar_chunks:
                if chunk_id in chunk_data:
                    chunk, doc = chunk_data[chunk_id]
                    results.append(ChunkResult(
                        id=chunk.id,
                        text=chunk.text,
                        chunk_index=chunk.chunk_index,
                        document_id=chunk.document_id,
                        filename=doc.filename,
                        similarity_score=similarity_score
                    ))
            
            return SearchResponse(
                query=request.query,
                results=results,
                total_results=len(results)
            )
            
        finally:
            session.close()
            
    except Exception as e:
        raise HTTPException(500, f"Search failed: {str(e)}")

@app.post("/embed")
async def trigger_embedding(document_id: Optional[int] = None):
    """Trigger embedding job for documents"""
    try:
        if document_id:
            q.enqueue("jobs.embed_chunks.run", document_id=document_id)
            return {"status": "embedding_queued", "document_id": document_id}
        else:
            q.enqueue("jobs.embed_chunks.run")
            return {"status": "embedding_queued", "message": "All unembedded chunks queued"}
    except Exception as e:
        raise HTTPException(500, f"Failed to queue embedding job: {str(e)}")
