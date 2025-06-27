"""
MUED Snowflake AI App 用 FastAPI アプリケーション
記事推薦のためのREST APIを提供
"""

from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from snowflake.snowpark import Session

from api.models import ArticleRecommendation, HealthResponse, RecommendationResponse
from src.config import get_snowflake_session

# グローバルセッション変数
snowflake_session: Optional[Session] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクルを管理"""
    global snowflake_session
    # 起動時の処理
    try:
        snowflake_session = get_snowflake_session()
        print(" Connected to Snowflake")
    except Exception as e:
        print(f"L Failed to connect to Snowflake: {e}")
        raise

    yield

    # 終了時の処理
    if snowflake_session:
        snowflake_session.close()
        print(" Closed Snowflake connection")


# FastAPIアプリケーションの作成
app = FastAPI(
    title="MUED Snowflake AI App API",
    description="Snowflake Cortexを使用したブログ記事推薦のREST API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORSミドルウェアの追加
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_random_recommendations(session: Session, limit: int = 5) -> list[dict]:
    """
    特定のクエリがない場合にランダムな推薦を取得

    Args:
        session: Snowflakeセッション
        limit: 推薦数

    Returns:
        推薦辞書のリスト
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
        raise HTTPException(status_code=500, detail=f"データベースエラー: {str(e)}")


# Cortexの利用可能性の設定
USE_CORTEX = False  # TODO: SnowflakeアカウントでCortexが利用可能になったらTrueに設定


def get_similar_recommendations(
    session: Session, query: str, limit: int = 5
) -> list[dict]:
    """
    類似度に基づいて推薦を取得

    Args:
        session: Snowflakeセッション
        query: 検索クエリ
        limit: 推薦数

    Returns:
        推薦辞書のリスト
    """
    try:
        safe_query = query.replace("'", "''")

        if USE_CORTEX:
            # ========== CORTEXバージョン（ベクトル検索） ==========
            # クエリの埋め込みを生成
            query_embedding_sql = f"""
            SELECT SNOWFLAKE.CORTEX.EMBED_TEXT_768(
                'e5-base-v2',
                '{safe_query}'
            ) as query_emb
            """

            # ベクトル類似度を使用して類似記事を検索
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
            # ========== 現在のバージョン（テキスト検索） ==========
            # フォールバックとしてのテキストベース検索
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

        # 辞書に変換し、スコアがfloatであることを保証
        recommendations = []
        for _, row in results.iterrows():
            rec = row.to_dict()
            rec["score"] = float(rec["score"])
            recommendations.append(rec)

        return recommendations

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"検索エラー: {str(e)}")


@app.get("/", tags=["Root"])
async def root():
    """ルートエンドポイント"""
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
    """APIとデータベースのヘルスチェック"""
    try:
        # データベース接続のテスト
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
    student_id: str = Query(..., description="学生ID"),
    query: Optional[str] = Query(None, description="オプションの検索クエリ"),
    limit: int = Query(5, ge=1, le=20, description="推薦数"),
):
    """
    学生向けの記事推薦を取得

    - **student_id**: 必須の学生ID
    - **query**: セマンティック検索用のオプションクエリ
    - **limit**: 推薦数 (1-20、デフォルト: 5)

    クエリがない場合はランダムな推薦を返します。
    クエリがある場合は意味的に類似した記事を返します。
    """
    if not snowflake_session:
        raise HTTPException(status_code=503, detail="データベース接続が利用できません")

    try:
        # クエリの有無に基づいて推薦を取得
        if query:
            recommendations_data = get_similar_recommendations(
                snowflake_session, query, limit
            )
        else:
            recommendations_data = get_random_recommendations(snowflake_session, limit)

        # Pydanticモデルに変換
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
        raise HTTPException(status_code=500, detail=f"推薦の生成に失敗しました: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
