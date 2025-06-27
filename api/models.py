"""
Pydantic models for API responses
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ArticleRecommendation(BaseModel):
    """Single article recommendation"""

    article_id: str = Field(..., description="Unique article identifier")
    score: float = Field(..., ge=0.0, le=1.0, description="Similarity score (0-1)")
    title: Optional[str] = Field(None, description="Article title")
    summary: Optional[str] = Field(None, description="Article summary")
    url: Optional[str] = Field(None, description="Article URL")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "article_id": "n123456789",
                "score": 0.95,
                "title": "Pythonでデータ分析入門",
                "summary": "この記事では、Pythonを使ったデータ分析の基本について解説します。",
                "url": "https://note.com/user/n/n123456789",
            }
        }
    )


class RecommendationRequest(BaseModel):
    """Request model for recommendations"""

    student_id: str = Field(..., description="Student identifier")
    query: Optional[str] = Field(None, description="Optional search query")
    limit: int = Field(5, ge=1, le=20, description="Number of recommendations")


class RecommendationResponse(BaseModel):
    """Response model for recommendations"""

    student_id: str = Field(..., description="Student identifier")
    recommendations: list[ArticleRecommendation] = Field(
        ..., description="List of recommended articles"
    )
    total_count: int = Field(..., description="Total number of recommendations")
    generated_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when recommendations were generated",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "student_id": "12345",
                "recommendations": [
                    {
                        "article_id": "n123456789",
                        "score": 0.95,
                        "title": "Pythonでデータ分析入門",
                        "summary": "Pythonを使ったデータ分析の基本について解説。",
                        "url": "https://note.com/user/n/n123456789",
                    }
                ],
                "total_count": 1,
                "generated_at": "2024-06-27T10:30:00",
            }
        }
    )


class HealthResponse(BaseModel):
    """Health check response"""

    status: str = Field("healthy", description="Service status")
    database_connected: bool = Field(..., description="Database connection status")
    version: str = Field("1.0.0", description="API version")
