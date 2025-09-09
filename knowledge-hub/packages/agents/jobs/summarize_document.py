import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from packages.db.models import Document, Chunk
import httpx

OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://ollama:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3')
SUMMARY_MAX_TOKENS = int(os.getenv('SUMMARY_MAX_TOKENS','256'))

SYS = (
    "You write concise, faithful summaries using only the provided content. "
    "Avoid speculation and include key themes, entities, and any decisions or action items if present."
)

CHUNK_PROMPT = "Summarize this chunk in 1-2 sentences focusing on key facts and terms:\n{chunk}"
MERGE_PROMPT = (
    "Merge these chunk summaries into a clear 3-5 sentence summary. "
    "Keep it factual and grounded.\n\n{summaries}"
)

def _ollama(prompt: str, max_tokens: int):
    payload = { 'model': OLLAMA_MODEL, 'prompt': prompt, 'stream': False, 'options': { 'num_predict': max_tokens } }
    with httpx.Client(timeout=120) as client:
        r = client.post(f"{OLLAMA_URL}/api/generate", json=payload)
        r.raise_for_status()
        return r.json().get('response','').strip()

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
        # map: summarize chunks (cap to first N chars per chunk)
        partial_summaries = []
        for c in chunks[:20]:  # cap to 20 chunks for speed; tune later
            piece = c.text[:1200]
            s = _ollama(f"<system>\n{SYS}\n</system>\n<user>\n" + CHUNK_PROMPT.format(chunk=piece) + "\n</user>", max_tokens=128)
            if s:
                partial_summaries.append(f"- {s}")
        merged = _ollama(f"<system>\n{SYS}\n</system>\n<user>\n" + MERGE_PROMPT.format(summaries='\n'.join(partial_summaries)) + "\n</user>", max_tokens=SUMMARY_MAX_TOKENS)
        doc.summary = merged[:4000]
        session.commit()
    finally:
        session.close()