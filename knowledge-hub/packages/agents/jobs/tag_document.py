import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from packages.db.models import Document, Chunk, DocumentTag
import httpx

OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://ollama:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3')
TAG_LABELS = [s.strip() for s in os.getenv('TAG_LABELS','').split(',') if s.strip()]
MAX_CTX = int(os.getenv('TAG_CTX_CHARS', '6000'))

SYSTEM = (
    "You assign concise topic tags to documents using the provided labels only. "
    "Return 2-4 tags from the allowed list. If unsure, choose the closest labels. "
    "Respond as a JSON array of strings only."
)

PROMPT = (
    "Allowed labels: {labels}\n\n"
    "Document excerpt (may be partial):\n{excerpt}\n\n"
    "Return 2-4 labels as JSON array."
)

def _concat_context(chunks):
    buf = []
    total = 0
    for c in chunks:
        t = c.text[:1200]
        if total + len(t) > MAX_CTX: break
        buf.append(t)
        total += len(t)
    return "\n\n".join(buf)

def run(document_id: int):
    db_url = os.getenv('DATABASE_URL', 'postgresql+psycopg://hub:hub@db:5432/hub')
    engine = create_engine(db_url, pool_pre_ping=True)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = Session()
    try:
        doc = session.query(Document).get(document_id)
        if not doc:
            return
        chunks = session.query(Chunk).filter(Chunk.document_id==document_id).order_by(Chunk.chunk_index).all()
        if not chunks:
            return
        excerpt = _concat_context(chunks)
        payload = {
            'model': OLLAMA_MODEL,
            'prompt': f"<system>\n{SYSTEM}\n</system>\n<user>\n" + PROMPT.format(labels=', '.join(TAG_LABELS), excerpt=excerpt) + "\n</user>",
            'stream': False,
            'options': { 'num_predict': 128 }
        }
        with httpx.Client(timeout=120) as client:
            r = client.post(f"{OLLAMA_URL}/api/generate", json=payload)
            r.raise_for_status()
            text = r.json().get('response','[]').strip()
        # naive JSON parse
        import json
        tags = []
        try:
            tags = json.loads(text)
            if not isinstance(tags, list):
                tags = []
        except Exception:
            # fallback: split by commas
            tags = [t.strip().strip('[]"\'') for t in text.split(',') if t.strip()]
        # clear old tags
        session.query(DocumentTag).filter(DocumentTag.document_id==document_id).delete()
        for t in tags[:4]:
            if t:
                session.add(DocumentTag(document_id=document_id, tag=str(t)[:128]))
        session.commit()
    finally:
        session.close()