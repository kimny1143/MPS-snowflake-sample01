import os
from typing import List, Optional
import numpy as np
from openai import OpenAI
from snowflake.snowpark import Session
import json

from .config import get_session
from .models import LoadResult


def get_openai_client() -> OpenAI:
    """Initialize OpenAI client"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    return OpenAI(api_key=api_key)


def create_embedding(text: str, model: str = "text-embedding-3-small") -> List[float]:
    """Create embedding for text using OpenAI API"""
    client = get_openai_client()
    response = client.embeddings.create(
        input=text,
        model=model
    )
    return response.data[0].embedding


def create_embeddings_batch(texts: List[str], model: str = "text-embedding-3-small") -> List[List[float]]:
    """Create embeddings for multiple texts"""
    client = get_openai_client()
    response = client.embeddings.create(
        input=texts,
        model=model
    )
    return [item.embedding for item in response.data]


def generate_article_embeddings(session: Session) -> dict:
    """Generate embeddings for all article chunks"""
    try:
        # First create chunks
        session.sql("CALL STG.CREATE_ARTICLE_CHUNKS()").collect()
        
        # Get chunks that need embeddings
        chunks_df = session.sql("""
            SELECT c.CHUNK_ID, c.CHUNK_TEXT
            FROM STG.ARTICLE_CHUNKS c
            LEFT JOIN STG.ARTICLE_EMBEDDINGS e ON c.CHUNK_ID = e.CHUNK_ID
            WHERE e.CHUNK_ID IS NULL
            LIMIT 100
        """).to_pandas()
        
        if chunks_df.empty:
            return {
                "status": "success",
                "message": "No chunks to process",
                "embeddings_created": 0
            }
        
        # Create embeddings in batches
        batch_size = 20
        embeddings_created = 0
        
        for i in range(0, len(chunks_df), batch_size):
            batch = chunks_df.iloc[i:i+batch_size]
            texts = batch['CHUNK_TEXT'].tolist()
            chunk_ids = batch['CHUNK_ID'].tolist()
            
            embeddings = create_embeddings_batch(texts)
            
            # Insert embeddings
            for chunk_id, embedding in zip(chunk_ids, embeddings):
                session.sql(f"""
                    INSERT INTO STG.ARTICLE_EMBEDDINGS (CHUNK_ID, EMBEDDING_VECTOR)
                    SELECT '{chunk_id}', PARSE_JSON('{json.dumps(embedding)}')
                """).collect()
                embeddings_created += 1
        
        return {
            "status": "success",
            "message": f"Created {embeddings_created} embeddings",
            "embeddings_created": embeddings_created
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def semantic_search(session: Session, query: str, limit: int = 10) -> List[dict]:
    """Perform semantic search using cosine similarity"""
    # Create embedding for query
    query_embedding = create_embedding(query)
    
    # Search using cosine similarity
    results = session.sql(f"""
        WITH query_embedding AS (
            SELECT PARSE_JSON('{json.dumps(query_embedding)}') as vec
        )
        SELECT 
            s.ARTICLE_ID,
            s.TITLE,
            s.URL,
            s.PUBLISHED_AT,
            s.CHUNK_TEXT,
            STG.COSINE_SIMILARITY(s.EMBEDDING_VECTOR, q.vec) as similarity
        FROM STG.SEARCHABLE_ARTICLES s, query_embedding q
        WHERE similarity > 0.7
        ORDER BY similarity DESC
        LIMIT {limit}
    """).to_pandas()
    
    return results.to_dict('records')