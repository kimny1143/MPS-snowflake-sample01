"""
FastAPI application for MUED Snowflake AI App
Provides REST API for article recommendations
"""

from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from api.models import ArticleRecommendation, HealthResponse, RecommendationResponse
from snowflake.snowpark import Session
from src.config import get_snowflake_session

# Global session variable
snowflake_session: Optional[Session] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global snowflake_session
    # Startup
    try:
        snowflake_session = get_snowflake_session()
        print(" Connected to Snowflake")
    except Exception as e:
        print(f"L Failed to connect to Snowflake: {e}")
        raise

    yield

    # Shutdown
    if snowflake_session:
        snowflake_session.close()
        print(" Closed Snowflake connection")


# Create FastAPI app
app = FastAPI(
    title="MUED Snowflake AI App API",
    description="REST API for blog post recommendations using Snowflake Cortex",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_random_recommendations(session: Session, limit: int = 5) -> list[dict]:
    """
    Get random recommendations when no specific query is provided

    Args:
        session: Snowflake session
        limit: Number of recommendations

    Returns:
        List of recommendation dictionaries
    """
    sql = f"""
    SELECT
        id as article_id,
        1.0 as score,
        title,
        summary,
        url
    FROM BLOG_POSTS
    WHERE summary IS NOT NULL
    ORDER BY RANDOM()
    LIMIT {limit}
    """

    try:
        results = session.sql(sql).to_pandas()
        return results.to_dict("records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# Configuration for Cortex availability
USE_CORTEX = (
    False  # TODO: Set to True when Cortex is available in your Snowflake account
)


def get_similar_recommendations(
    session: Session, query: str, limit: int = 5
) -> list[dict]:
    """
    Get recommendations based on similarity

    Args:
        session: Snowflake session
        query: Search query
        limit: Number of recommendations

    Returns:
        List of recommendation dictionaries
    """
    try:
        safe_query = query.replace("'", "''")

        if USE_CORTEX:
            # ========== CORTEX VERSION (Vector Search) ==========
            # Generate embedding for the query
            query_embedding_sql = f"""
            SELECT SNOWFLAKE.CORTEX.EMBED_TEXT_768(
                'e5-base-v2',
                '{safe_query}'
            ) as query_emb
            """

            # Search for similar posts using vector similarity
            search_sql = f"""
            WITH query_vector AS (
                {query_embedding_sql}
            )
            SELECT
                b.id as article_id,
                VECTOR_COSINE_DISTANCE(b.emb, q.query_emb) as score,
                b.title,
                b.summary,
                b.url
            FROM BLOG_POSTS b, query_vector q
            WHERE b.emb IS NOT NULL
              AND b.summary IS NOT NULL
            ORDER BY score DESC
            LIMIT {limit}
            """
        else:
            # ========== CURRENT VERSION (Text Search) ==========
            # Text-based search as fallback
            search_sql = f"""
            SELECT
                id as article_id,
                CASE
                    WHEN LOWER(title) LIKE LOWER('%{safe_query}%') THEN 1.0
                    WHEN LOWER(summary) LIKE LOWER('%{safe_query}%') THEN 0.7
                    WHEN LOWER(body_markdown) LIKE LOWER('%{safe_query}%') THEN 0.5
                    ELSE 0.0
                END as score,
                title,
                summary,
                url
            FROM BLOG_POSTS
            WHERE
                summary IS NOT NULL
                AND (
                    LOWER(title) LIKE LOWER('%{safe_query}%')
                    OR LOWER(summary) LIKE LOWER('%{safe_query}%')
                    OR LOWER(body_markdown) LIKE LOWER('%{safe_query}%')
                )
            ORDER BY
                score DESC,
                published_at DESC
            LIMIT {limit}
            """

        results = session.sql(search_sql).to_pandas()

        # Convert to dict and ensure score is float
        recommendations = []
        for _, row in results.iterrows():
            rec = row.to_dict()
            rec["score"] = float(rec["score"])
            recommendations.append(rec)

        return recommendations

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "MUED Snowflake AI App API",
        "version": "1.0.0",
        "endpoints": {
            "recommendations": "/recommend",
            "health": "/health",
            "docs": "/docs",
        },
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Check API and database health"""
    try:
        # Test database connection
        if snowflake_session:
            result = snowflake_session.sql("SELECT 1").collect()
            db_connected = len(result) > 0
        else:
            db_connected = False

    except Exception:
        db_connected = False

    return HealthResponse(
        status="healthy" if db_connected else "degraded",
        database_connected=db_connected,
        version="1.0.0",
    )


@app.get("/recommend", response_model=RecommendationResponse, tags=["Recommendations"])
async def get_recommendations(
    student_id: str = Query(..., description="Student identifier"),
    query: Optional[str] = Query(None, description="Optional search query"),
    limit: int = Query(5, ge=1, le=20, description="Number of recommendations"),
):
    """
    Get article recommendations for a student

    - **student_id**: Required student identifier
    - **query**: Optional search query for semantic search
    - **limit**: Number of recommendations (1-20, default: 5)

    If no query is provided, returns random recommendations.
    If query is provided, returns semantically similar articles.
    """
    if not snowflake_session:
        raise HTTPException(status_code=503, detail="Database connection not available")

    try:
        # Get recommendations based on whether query is provided
        if query:
            recommendations_data = get_similar_recommendations(
                snowflake_session, query, limit
            )
        else:
            recommendations_data = get_random_recommendations(snowflake_session, limit)

        # Convert to Pydantic models
        recommendations = [ArticleRecommendation(**rec) for rec in recommendations_data]

        return RecommendationResponse(
            student_id=student_id,
            recommendations=recommendations,
            total_count=len(recommendations),
            generated_at=datetime.now(),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate recommendations: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
