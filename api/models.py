"""
APIレスポンス用Pydanticモデル
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ArticleRecommendation(BaseModel):
    """単一の記事推薦"""

    article_id: str = Field(..., description="ユニークな記事ID")
    score: float = Field(..., ge=0.0, le=1.0, description="類似度スコア (0-1)")
    title: Optional[str] = Field(None, description="記事タイトル")
    summary: Optional[str] = Field(None, description="記事の要約")
    url: Optional[str] = Field(None, description="記事URL")

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
    """推薦リクエストモデル"""

    student_id: str = Field(..., description="学生ID")
    query: Optional[str] = Field(None, description="オプションの検索クエリ")
    limit: int = Field(5, ge=1, le=20, description="推薦数")


class RecommendationResponse(BaseModel):
    """推薦レスポンスモデル"""

    student_id: str = Field(..., description="学生ID")
    recommendations: list[ArticleRecommendation] = Field(..., description="推薦記事のリスト")
    total_count: int = Field(..., description="推薦総数")
    generated_at: datetime = Field(
        default_factory=datetime.now,
        description="推薦生成日時",
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
    """ヘルスチェックレスポンス"""

    status: str = Field("healthy", description="サービス状態")
    database_connected: bool = Field(..., description="データベース接続状態")
    version: str = Field("1.0.0", description="APIバージョン")
