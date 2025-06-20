import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import get_session
from src.loader import load_rss_to_raw, execute_merge, get_task_status
from src.embeddings import generate_article_embeddings, semantic_search


st.set_page_config(
    page_title="Note RSS → Snowflake RAG",
    page_icon="❄️",
    layout="wide"
)

st.title("❄️ Note RSS → Snowflake RAG Pipeline")
st.markdown("RSS取込から検索まで、Snowflakeで完結するRAGデモ")


def init_session():
    """Initialize Snowflake session"""
    if 'snowflake_session' not in st.session_state:
        try:
            st.session_state.snowflake_session = get_session()
            st.success("✅ Snowflake接続成功")
        except Exception as e:
            st.error(f"❌ Snowflake接続エラー: {e}")
            st.stop()
    return st.session_state.snowflake_session


def main():
    session = init_session()
    
    # Sidebar
    with st.sidebar:
        st.header("📊 システム状態")
        
        if st.button("🔄 ステータス更新"):
            st.rerun()
        
        # Show data counts
        try:
            raw_count = session.sql("SELECT COUNT(*) as cnt FROM RAW.NOTE_RSS_RAW").collect()[0]['CNT']
            core_count = session.sql("SELECT COUNT(*) as cnt FROM CORE.BLOG_POSTS").collect()[0]['CNT']
            chunk_count = session.sql("SELECT COUNT(*) as cnt FROM STG.ARTICLE_CHUNKS").collect()[0]['CNT']
            embedding_count = session.sql("SELECT COUNT(*) as cnt FROM STG.ARTICLE_EMBEDDINGS").collect()[0]['CNT']
            
            col1, col2 = st.columns(2)
            col1.metric("RAW記事", raw_count)
            col2.metric("CORE記事", core_count)
            col1.metric("チャンク数", chunk_count)
            col2.metric("埋め込み数", embedding_count)
            
        except Exception as e:
            st.error(f"データ取得エラー: {e}")
        
        # Show task status
        st.subheader("⚙️ タスク状態")
        try:
            task_df = get_task_status(session)
            if not task_df.empty:
                for _, task in task_df.iterrows():
                    status_icon = "🟢" if task['state'] == 'started' else "🔴"
                    st.text(f"{status_icon} {task['name']}")
        except:
            st.text("タスク情報取得不可")
    
    # Main content
    tab1, tab2, tab3, tab4 = st.tabs(["📥 RSS取込", "🔍 セマンティック検索", "📈 データ分析", "⚙️ 管理"])
    
    with tab1:
        st.header("RSS フィード取込")
        
        feed_url = st.text_input(
            "RSS URL", 
            value="https://note.com/mued_glasswerks/rss",
            help="取り込むRSSフィードのURL"
        )
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🚀 RSS取込実行", type="primary"):
                with st.spinner("取込中..."):
                    result = load_rss_to_raw(session, feed_url)
                    if result['status'] == 'success':
                        st.success(f"✅ {result['rows_loaded']}件の記事を取込")
                        
                        merge_result = execute_merge(session)
                        if merge_result['status'] == 'success':
                            st.info(f"📊 {merge_result['message']}")
                    else:
                        st.error(f"❌ エラー: {result['error']}")
        
        with col2:
            if st.button("🔄 手動マージ"):
                with st.spinner("マージ実行中..."):
                    result = execute_merge(session)
                    if result['status'] == 'success':
                        st.success(result['message'])
                    else:
                        st.error(f"エラー: {result['error']}")
        
        with col3:
            if st.button("🤖 埋め込み生成"):
                with st.spinner("OpenAI APIで埋め込み生成中..."):
                    result = generate_article_embeddings(session)
                    if result['status'] == 'success':
                        st.success(f"✅ {result['embeddings_created']}件の埋め込みを生成")
                    else:
                        st.error(f"❌ エラー: {result['error']}")
    
    with tab2:
        st.header("セマンティック検索")
        st.markdown("OpenAI Embeddingを使用した類似記事検索")
        
        query = st.text_input("検索クエリ", placeholder="例: Snowflakeの使い方")
        
        if st.button("🔍 検索実行", type="primary"):
            if query:
                with st.spinner("検索中..."):
                    try:
                        results = semantic_search(session, query, limit=10)
                        
                        if results:
                            st.success(f"{len(results)}件の関連記事が見つかりました")
                            
                            for i, result in enumerate(results):
                                with st.expander(f"📄 {result['TITLE']} (類似度: {result['similarity']:.3f})"):
                                    st.markdown(f"**URL**: {result['URL']}")
                                    st.markdown(f"**公開日**: {result['PUBLISHED_AT']}")
                                    st.markdown("---")
                                    st.markdown(result['CHUNK_TEXT'][:500] + "...")
                        else:
                            st.info("関連記事が見つかりませんでした")
                    except Exception as e:
                        st.error(f"検索エラー: {e}")
                        st.info("埋め込みが生成されているか確認してください")
            else:
                st.warning("検索クエリを入力してください")
    
    with tab3:
        st.header("データ分析")
        
        # Recent articles
        st.subheader("📰 最近の記事")
        try:
            recent_df = session.sql("""
                SELECT TITLE, URL, PUBLISHED_AT, BODY_LENGTH
                FROM CORE.BLOG_POSTS
                ORDER BY PUBLISHED_AT DESC
                LIMIT 20
            """).to_pandas()
            
            if not recent_df.empty:
                st.dataframe(recent_df, use_container_width=True)
                
                # Article length distribution
                fig = px.histogram(recent_df, x='BODY_LENGTH', 
                                 title="記事の長さ分布",
                                 labels={'BODY_LENGTH': '文字数', 'count': '記事数'})
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"データ取得エラー: {e}")
    
    with tab4:
        st.header("管理機能")
        
        # SQL Executor
        st.subheader("🗄️ SQLエグゼキューター")
        sql_query = st.text_area("SQL", height=100, value="SELECT * FROM CORE.BLOG_POSTS LIMIT 5")
        
        if st.button("▶️ 実行"):
            try:
                result_df = session.sql(sql_query).to_pandas()
                st.dataframe(result_df, use_container_width=True)
            except Exception as e:
                st.error(f"SQLエラー: {e}")
        
        # Setup embeddings
        st.subheader("🛠️ 埋め込みテーブルセットアップ")
        if st.button("埋め込みテーブル作成"):
            try:
                with open('../snowflake/embeddings.sql', 'r') as f:
                    for stmt in f.read().split(';'):
                        if stmt.strip():
                            session.sql(stmt).collect()
                st.success("✅ 埋め込みテーブル作成完了")
            except Exception as e:
                st.error(f"セットアップエラー: {e}")


if __name__ == "__main__":
    main()