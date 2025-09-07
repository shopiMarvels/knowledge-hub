import os
import pickle
import pathlib
import numpy as np
from typing import List
from sentence_transformers import SentenceTransformer
import faiss
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from packages.db.models import Document, Chunk

# Global model and index (loaded once per worker)
model = None
faiss_index = None
FAISS_INDEX_PATH = "/data/faiss_index.idx"
FAISS_MAPPING_PATH = "/data/faiss_mapping.pkl"

def get_model():
    """Load the sentence transformer model (cached)"""
    global model
    if model is None:
        print("Loading MiniLM model...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Model loaded successfully")
    return model

def get_faiss_index():
    """Load or create FAISS index"""
    global faiss_index
    if faiss_index is None:
        index_path = pathlib.Path(FAISS_INDEX_PATH)
        if index_path.exists():
            print("Loading existing FAISS index...")
            faiss_index = faiss.read_index(str(index_path))
            print(f"Loaded FAISS index with {faiss_index.ntotal} vectors")
        else:
            print("Creating new FAISS index...")
            # Create index for 384-dimensional vectors (MiniLM output size)
            faiss_index = faiss.IndexFlatIP(384)  # Inner Product for cosine similarity
            print("Created new FAISS index")
    return faiss_index

def get_faiss_mapping():
    """Load or create FAISS ID to chunk ID mapping"""
    mapping_path = pathlib.Path(FAISS_MAPPING_PATH)
    if mapping_path.exists():
        with open(mapping_path, 'rb') as f:
            return pickle.load(f)
    return {}

def save_faiss_index_and_mapping(index, mapping):
    """Save FAISS index and mapping to disk"""
    # Ensure directory exists
    pathlib.Path("/data").mkdir(exist_ok=True)
    
    # Save index
    faiss.write_index(index, FAISS_INDEX_PATH)
    
    # Save mapping
    with open(FAISS_MAPPING_PATH, 'wb') as f:
        pickle.dump(mapping, f)
    
    print(f"Saved FAISS index with {index.ntotal} vectors and mapping")

def run(document_id: int = None, chunk_id: int = None):
    """
    Embed chunks and add to FAISS index
    Args:
        document_id: Process all chunks for this document (optional)
        chunk_id: Process specific chunk (optional)
    """
    print(f"Starting embedding job - document_id: {document_id}, chunk_id: {chunk_id}")
    
    db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:password@db:5432/knowledge_hub')
    engine = create_engine(db_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = SessionLocal()
    
    try:
        # Load model and index
        model = get_model()
        index = get_faiss_index()
        mapping = get_faiss_mapping()
        
        # Get chunks to process
        query = session.query(Chunk).filter(Chunk.embedding_vector_id.is_(None))
        
        if document_id:
            query = query.filter(Chunk.document_id == document_id)
        elif chunk_id:
            query = query.filter(Chunk.id == chunk_id)
        
        chunks = query.all()
        
        if not chunks:
            print("No chunks to embed")
            return
        
        print(f"Processing {len(chunks)} chunks...")
        
        # Extract texts and generate embeddings
        texts = [chunk.text for chunk in chunks]
        embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        
        # Add embeddings to FAISS index
        start_idx = index.ntotal
        index.add(embeddings.astype(np.float32))
        
        # Update chunk records and mapping
        for i, chunk in enumerate(chunks):
            vector_id = start_idx + i
            chunk.embedding_vector_id = vector_id
            mapping[vector_id] = chunk.id
            
        session.commit()
        
        # Save updated index and mapping
        save_faiss_index_and_mapping(index, mapping)
        
        print(f"Successfully embedded {len(chunks)} chunks. Total vectors in index: {index.ntotal}")
        
    except Exception as e:
        session.rollback()
        print(f"Error in embed_chunks job: {e}")
        raise
    finally:
        session.close()

def search_similar_chunks(query_text: str, k: int = 5):
    """
    Search for similar chunks using FAISS
    Args:
        query_text: Text to search for
        k: Number of results to return
    Returns:
        List of (chunk_id, similarity_score) tuples
    """
    try:
        model = get_model()
        index = get_faiss_index()
        mapping = get_faiss_mapping()
        
        if index.ntotal == 0:
            return []
        
        # Encode query
        query_embedding = model.encode([query_text], convert_to_numpy=True, normalize_embeddings=True)
        
        # Search FAISS index
        scores, indices = index.search(query_embedding.astype(np.float32), k)
        
        # Convert to chunk IDs
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx in mapping:
                chunk_id = mapping[idx]
                results.append((chunk_id, float(score)))
        
        return results
        
    except Exception as e:
        print(f"Error in search_similar_chunks: {e}")
        return []
