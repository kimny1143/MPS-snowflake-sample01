"""
Streamlit UI for MUED Snowflake AI App
Simple vector search interface for blog posts
"""

import pandas as pd
import streamlit as st

from snowflake.snowpark import Session
from src.config import get_snowflake_session

st.set_page_config(page_title="MUED ブログ検索", page_icon="🔍", layout="wide")


@st.cache_resource
def init_snowflake_session() -> Session:
    """Initialize and cache Snowflake session"""
    return get_snowflake_session()


def search_similar_posts(session: Session, query: str, limit: int = 5) -> pd.DataFrame:
    """
    Search for similar blog posts

    Args:
        session: Snowflake session
        query: Search query text
        limit: Number of results to return

    Returns:
        DataFrame with similar posts
    """
    # Check if Cortex is available (can be toggled when account is upgraded)
    USE_CORTEX = (
        False  # TODO: Set to True when Cortex is available in your Snowflake account
    )

    try:
        # Escape single quotes in query
        safe_query = query.replace("'", "''")

        if USE_CORTEX:
            # ========== CORTEX VERSION (Vector Search) ==========
            # Uncomment and use this version when Cortex is available
            """
            # Generate embedding for the query using Cortex
            query_embedding_sql = f'''
            SELECT SNOWFLAKE.CORTEX.EMBED_TEXT_768(
                'e5-base-v2',
                '{safe_query}'
            ) as query_emb
            '''

            # Search for similar posts using vector similarity
            search_sql = f'''
            WITH query_vector AS (
                {query_embedding_sql}
            )
            SELECT
                b.id,
                b.title,
                b.summary,
                b.url,
                b.published_at,
                b.tags,
                VECTOR_COSINE_DISTANCE(b.emb, q.query_emb) as similarity_score
            FROM BLOG_POSTS b, query_vector q
            WHERE b.emb IS NOT NULL
            ORDER BY similarity_score DESC
            LIMIT {limit}
            '''
            """
            pass  # Remove this line when enabling Cortex
        else:
            # ========== CURRENT VERSION (Text Search) ==========
            # Traditional text-based search as fallback
            search_sql = f"""
            SELECT
                id,
                title,
                summary,
                url,
                published_at,
                tags,
                CASE
                    WHEN LOWER(title) LIKE LOWER('%{safe_query}%') THEN 1.0
                    WHEN LOWER(summary) LIKE LOWER('%{safe_query}%') THEN 0.7
                    WHEN LOWER(body_markdown) LIKE LOWER('%{safe_query}%') THEN 0.5
                    ELSE 0.0
                END as similarity_score
            FROM BLOG_POSTS
            WHERE
                LOWER(title) LIKE LOWER('%{safe_query}%')
                OR LOWER(summary) LIKE LOWER('%{safe_query}%')
                OR LOWER(body_markdown) LIKE LOWER('%{safe_query}%')
            ORDER BY
                similarity_score DESC,
                published_at DESC
            LIMIT {limit}
            """

        results = session.sql(search_sql).to_pandas()
        return results

    except Exception as e:
        st.error(f"検索エラー: {str(e)}")
        return pd.DataFrame()


def format_result_card(row: pd.Series) -> None:
    """Format and display a single search result"""
    with st.container():
        col1, col2 = st.columns([4, 1])

        with col1:
            st.markdown(f"### [{row['TITLE']}]({row['URL']})")
            st.markdown(f"**類似度スコア:** {row['SIMILARITY_SCORE']:.3f}")

            if pd.notna(row["SUMMARY"]):
                st.markdown(f"📝 {row['SUMMARY']}")

            if pd.notna(row["TAGS"]):
                tags = row["TAGS"] if isinstance(row["TAGS"], list) else []
                if tags:
                    st.markdown("🏷️ " + " ".join([f"`{tag}`" for tag in tags if tag]))

        with col2:
            if pd.notna(row["PUBLISHED_AT"]):
                pub_date = pd.to_datetime(row["PUBLISHED_AT"])
                st.caption(f"📅 {pub_date.strftime('%Y/%m/%d')}")

        st.divider()


def main():
    """Main Streamlit app"""
    st.title("🔍 MUED ブログ検索")
    st.markdown("キーワードを入力して、関連するブログ記事を検索します。")

    # Initialize session
    session = init_snowflake_session()

    # Search interface
    col1, col2 = st.columns([3, 1])

    with col1:
        query = st.text_input(
            "検索キーワード",
            placeholder="例: コード進行, Python, データ分析",
            help="検索したいトピックやキーワードを入力してください",
        )

    with col2:
        num_results = st.number_input(
            "表示件数", min_value=1, max_value=20, value=5, step=1
        )

    # Search button
    if st.button("🔍 検索", type="primary", use_container_width=True):
        if query:
            with st.spinner("検索中..."):
                results = search_similar_posts(session, query, num_results)

                if not results.empty:
                    st.success(f"{len(results)}件の関連記事が見つかりました")

                    # Display results
                    for _, row in results.iterrows():
                        format_result_card(row)
                else:
                    st.warning("関連する記事が見つかりませんでした")
        else:
            st.warning("検索キーワードを入力してください")

    # Sidebar with stats
    with st.sidebar:
        st.header("📊 統計情報")

        try:
            # Get post count
            post_count = session.sql(
                "SELECT COUNT(*) as cnt FROM BLOG_POSTS"
            ).collect()[0]["CNT"]
            st.metric("総記事数", f"{post_count:,}")

            # Get latest update
            latest_update = session.sql(
                "SELECT MAX(updated_at) as latest FROM BLOG_POSTS"
            ).collect()[0]["LATEST"]

            if latest_update:
                st.caption(f"最終更新: {latest_update.strftime('%Y/%m/%d %H:%M')}")

        except Exception as e:
            st.error(f"統計情報の取得に失敗しました: {str(e)}")

        st.divider()
        st.caption("Powered by Snowflake Cortex 🤖")


if __name__ == "__main__":
    main()
