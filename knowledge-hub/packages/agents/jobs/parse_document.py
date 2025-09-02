import os, pathlib
from typing import List
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from packages.db.models import Document, Chunk

# Optional token counter; fall back to char length
try:
    import tiktoken
    enc = tiktoken.get_encoding('cl100k_base')
    def count_tokens(text: str) -> int:
        return len(enc.encode(text))
except Exception:
    def count_tokens(text: str) -> int:
        return max(1, len(text)//4)  # rough estimate

# PDF/DOCX/TXT extractors
def extract_text(path: str) -> str:
    p = pathlib.Path(path)
    if p.suffix.lower() == '.pdf':
        import fitz  # PyMuPDF
        with fitz.open(path) as doc:
            return "\n".join(page.get_text("text") for page in doc)
    elif p.suffix.lower() == '.docx':
        import docx2txt
        return docx2txt.process(path) or ""
    elif p.suffix.lower() == '.txt':
        return pathlib.Path(path).read_text(encoding='utf-8', errors='ignore')
    else:
        return ""

# Simple recursive chunker
def chunk_text(text: str, max_tokens: int = 800, overlap: int = 120) -> List[str]:
    words = text.split()
    chunks, chunk = [], []
    curr_tokens = 0
    for w in words:
        t = count_tokens(w + ' ')
        if curr_tokens + t > max_tokens and chunk:
            chunks.append(' '.join(chunk))
            # start next with overlap
            if overlap > 0:
                tail = ' '.join(chunk)[-overlap*4:]  # approx chars for overlap
                chunk = tail.split()
                curr_tokens = count_tokens(' '.join(chunk))
            else:
                chunk = []
                curr_tokens = 0
        chunk.append(w)
        curr_tokens += t
    if chunk:
        chunks.append(' '.join(chunk))
    return [c.strip() for c in chunks if c.strip()]

# Entrypoint for RQ
def run(document_id: int, path: str, storage_dir: str):
    from sqlalchemy import text as sqltext
    db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:password@db:5432/knowledge_hub')
    engine = create_engine(db_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = SessionLocal()
    try:
        doc = session.query(Document).get(document_id)
        if not doc:
            print(f"Document {document_id} not found")
            return
        # Extract
        raw = extract_text(path) or ""
        if not raw.strip():
            doc.status = 'parsed_empty'
            session.commit()
            return
        # Chunk
        pieces = chunk_text(raw, max_tokens=800, overlap=120)
        # Insert chunks
        for i, text in enumerate(pieces):
            session.add(Chunk(document_id=document_id, chunk_index=i, text=text, token_count=count_tokens(text)))
        doc.status = 'parsed'
        session.commit()
        print(f"Parsed {len(pieces)} chunks for document {document_id}")
    except Exception as e:
        session.rollback()
        try:
            doc = session.query(Document).get(document_id)
            if doc:
                doc.status = 'error'
                session.commit()
        except Exception:
            pass
        print("parse_document error:", e)
    finally:
        session.close()
