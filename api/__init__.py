"""
MUED Snowflake AI App API Package
"""

from api.main import app
from api.models import (
    ArticleRecommendation,
    HealthResponse,
    RecommendationRequest,
    RecommendationResponse,
)

__version__ = "1.0.0"
__all__ = [
    "app",
    "ArticleRecommendation",
    "RecommendationRequest",
    "RecommendationResponse",
    "HealthResponse",
]
