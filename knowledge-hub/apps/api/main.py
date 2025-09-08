from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from redis import Redis
from rq import Queue
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import List, Optional
import os, pathlib, uuid, re

from packages.db.models import Base
from packages.db.models import Document, Chunk  # (we'll add these in step 4)

APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@db:5432/knowledge_hub")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
STORAGE_DIR = os.getenv("STORAGE_DIR", "/data")
MIN_SIM = float(os.getenv("MIN_SIM", "0.15"))  # threshold for low-confidence

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

class QARequest(BaseModel):
    query: str
    k: int = 5
    max_tokens: int = 384

class Citation(BaseModel):
    document_id: int
    chunk_index: int

class ContextHit(BaseModel):
    document_id: int
    chunk_index: int
    score: float
    preview: str

class QAResponse(BaseModel):
    answer: str
    citations: List[Citation]
    hits: List[ContextHit]

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

@app.post("/qa", response_model=QAResponse)
async def qa(req: QARequest):
    """Question & Answer endpoint with citations"""
    try:
        # Import here to avoid startup issues if FAISS files don't exist yet
        from apps.api.retrieval import retrieve_topk
        from apps.api.llm import generate_answer
        
        session = SessionLocal()
        try:
            # Retrieve relevant chunks
            results = retrieve_topk(session, req.query, k=req.k)
            
            if not results:
                return QAResponse(
                    answer="I don't have any relevant information to answer that question. Please try uploading some documents first or rephrase your question.",
                    citations=[],
                    hits=[]
                )
            
            # Filter by similarity threshold and build tagged contexts
            tagged_contexts = []
            valid_results = []
            
            for chunk, score in results:
                if score < MIN_SIM:
                    continue
                    
                # Get document info for better context tags
                document = session.query(Document).filter(Document.id == chunk.document_id).first()
                if document:
                    tag = f"Doc {chunk.document_id} #{chunk.chunk_index}"
                    # Keep contexts short to fit model context window
                    text = chunk.text[:1800] if len(chunk.text) > 1800 else chunk.text
                    tagged_contexts.append((tag, text))
                    valid_results.append((chunk, score, document))
            
            if not tagged_contexts:
                return QAResponse(
                    answer="I found some potentially relevant information, but it doesn't seem closely related enough to your question. Please try rephrasing or being more specific.",
                    citations=[],
                    hits=[]
                )
            
            # Generate answer using LLM
            answer = await generate_answer(req.query, tagged_contexts, max_tokens=req.max_tokens)
            
            # Extract citations from answer using regex
            citation_matches = re.findall(r"\(Doc (\d+) #(\d+)\)", answer)
            citations = [
                Citation(document_id=int(doc_id), chunk_index=int(chunk_idx))
                for doc_id, chunk_idx in set(citation_matches)  # Remove duplicates
            ]
            
            # Prepare context hits for UI
            hits = [
                ContextHit(
                    document_id=chunk.document_id,
                    chunk_index=chunk.chunk_index,
                    score=float(score),
                    preview=chunk.text[:240] + "..." if len(chunk.text) > 240 else chunk.text
                )
                for chunk, score, document in valid_results[:6]  # Limit to top 6 for UI
            ]
            
            return QAResponse(
                answer=answer,
                citations=citations,
                hits=hits
            )
            
        finally:
            session.close()
            
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=503, 
            detail="Embedding system not ready. Please ensure documents have been embedded first."
        )
    except Exception as e:
        print(f"Error in Q&A endpoint: {e}")
        raise HTTPException(500, f"Q&A failed: {str(e)}")
