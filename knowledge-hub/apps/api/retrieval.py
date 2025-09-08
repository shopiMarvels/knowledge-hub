# apps/api/retrieval.py
import os
import faiss
import pickle
import pathlib
import numpy as np
from sqlalchemy.orm import Session
from sentence_transformers import SentenceTransformer
from packages.db.models import Chunk

MODEL_NAME = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "/data/faiss_index.idx")
FAISS_MAPPING_PATH = os.getenv("FAISS_MAPPING_PATH", "/data/faiss_mapping.pkl")

_model = None
_index = None
_mapping = None

def get_model():
    global _model
    if _model is None:
        print(f"Loading embedding model: {MODEL_NAME}")
        _model = SentenceTransformer(MODEL_NAME)
        print("Embedding model loaded successfully")
    return _model

def get_index():
    global _index
    if _index is None:
        index_path = pathlib.Path(FAISS_INDEX_PATH)
        if index_path.exists():
            print(f"Loading FAISS index from {FAISS_INDEX_PATH}")
            _index = faiss.read_index(str(index_path))
            print(f"FAISS index loaded with {_index.ntotal} vectors")
        else:
            raise FileNotFoundError(f"FAISS index not found at {FAISS_INDEX_PATH}")
    return _index

def get_mapping():
    global _mapping
    if _mapping is None:
        mapping_path = pathlib.Path(FAISS_MAPPING_PATH)
        if mapping_path.exists():
            with open(mapping_path, 'rb') as f:
                _mapping = pickle.load(f)
            print(f"FAISS mapping loaded with {len(_mapping)} entries")
        else:
            raise FileNotFoundError(f"FAISS mapping not found at {FAISS_MAPPING_PATH}")
    return _mapping

def retrieve_topk(session: Session, query: str, k: int = 5):
    """
    Retrieve top-k most similar chunks for a query
    Returns list[(chunk, score)] with score in [0,1] cosine similarity
    """
    try:
        model = get_model()
        index = get_index()
        mapping = get_mapping()
        
        # Encode query with same normalization as training
        q_emb = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
        
        # Search FAISS index
        scores, indices = index.search(q_emb.astype(np.float32), k)
        
        # Convert FAISS results to chunk objects
        results = []
        for score, faiss_idx in zip(scores[0], indices[0]):
            if faiss_idx == -1:  # FAISS returns -1 for empty slots
                continue
                
            # Map FAISS index to chunk ID
            chunk_id = mapping.get(faiss_idx)
            if chunk_id is None:
                continue
                
            # Get chunk from database
            chunk = session.query(Chunk).filter(Chunk.id == chunk_id).first()
            if chunk is None:
                continue
                
            # Normalize score (FAISS returns cosine similarity for normalized vectors)
            normalized_score = float(score)
            results.append((chunk, normalized_score))
        
        print(f"Retrieved {len(results)} chunks for query: '{query[:50]}...'")
        return results
        
    except Exception as e:
        print(f"Error in retrieve_topk: {e}")
        return []
