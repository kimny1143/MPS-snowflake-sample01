#!/usr/bin/env python
"""Enhance articles with AI-generated content and keywords"""

import sys

sys.path.insert(0, ".")

from src.config import get_session
from src.embeddings import get_openai_client


def generate_keywords_from_title(title: str, summary: str) -> list:
    """Generate relevant keywords from title and summary using AI"""
    try:
        client = get_openai_client()

        prompt = f"""
        記事タイトル: {title}
        要約: {summary}

        この音楽制作に関する記事から、関連するキーワードを10個生成してください。
        音楽制作、レコーディング、DTM、楽器、機材などに関連するキーワードを含めてください。
        カンマ区切りで出力してください。
        """

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
        )

        keywords = response.choices[0].message.content.strip().split(",")
        return [k.strip() for k in keywords]

    except Exception as e:
        print(f"Error generating keywords: {e}")
        return []


def enhance_article_content(session):
    """Enhance articles with generated content"""
    try:
        # 記事を取得
        articles = session.sql(
            """
            SELECT ID, TITLE, URL, BODY
            FROM CORE.BLOG_POSTS
            WHERE LENGTH(BODY) < 300
            LIMIT 5
        """
        ).collect()

        client = get_openai_client()

        for article in articles:
            print(f"\nEnhancing: {article['TITLE']}")

            # キーワード生成
            keywords = generate_keywords_from_title(article["TITLE"], article["BODY"])
            print(f"Keywords: {', '.join(keywords)}")

            # 拡張コンテンツ生成
            prompt = f"""
            以下の音楽制作記事の要約を元に、想定される内容を200文字程度で拡張してください：

            タイトル: {article['TITLE']}
            要約: {article['BODY']}

            音楽制作、レコーディング、機材などの観点から内容を推測して拡張してください。
            """

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
            )

            enhanced_content = response.choices[0].message.content.strip()

            # 元の要約 + AI生成コンテンツ + キーワード
            full_content = f"{article['BODY']}\n\n[AI拡張コンテンツ]\n{enhanced_content}\n\n[関連キーワード]\n{', '.join(keywords)}"

            # データベース更新
            session.sql(
                f"""
                UPDATE CORE.BLOG_POSTS
                SET BODY = '{full_content.replace("'", "''")}'
                WHERE ID = '{article['ID']}'
            """
            ).collect()

            print("✓ Enhanced with AI content")

    except Exception as e:
        print(f"Error: {e}")


def create_smart_chunks(session):
    """Create smarter chunks based on title and enhanced content"""
    try:
        print("\nCreating smart chunks...")

        # 既存のチャンクをクリア
        session.sql("DELETE FROM STG.ARTICLE_CHUNKS").collect()

        # タイトルベースのチャンク + コンテンツチャンク
        result = session.sql(
            """
            INSERT INTO STG.ARTICLE_CHUNKS (ARTICLE_ID, ARTICLE_URL, CHUNK_INDEX, CHUNK_TEXT, CHUNK_LENGTH)
            WITH article_chunks AS (
                -- タイトルをチャンクとして追加
                SELECT
                    ID as ARTICLE_ID,
                    URL as ARTICLE_URL,
                    0 as CHUNK_INDEX,
                    CONCAT('記事タイトル: ', TITLE) as CHUNK_TEXT
                FROM CORE.BLOG_POSTS

                UNION ALL

                -- 本文をチャンクとして追加
                SELECT
                    ID as ARTICLE_ID,
                    URL as ARTICLE_URL,
                    SEQ4() + 1 as CHUNK_INDEX,
                    value as CHUNK_TEXT
                FROM CORE.BLOG_POSTS,
                LATERAL SPLIT_TO_TABLE(BODY, '\n\n')
                WHERE LENGTH(TRIM(value)) > 30
            )
            SELECT
                ARTICLE_ID,
                ARTICLE_URL,
                CHUNK_INDEX,
                CHUNK_TEXT,
                LENGTH(CHUNK_TEXT) as CHUNK_LENGTH
            FROM article_chunks
        """
        ).collect()

        chunk_count = session.sql(
            "SELECT COUNT(*) as cnt FROM STG.ARTICLE_CHUNKS"
        ).collect()
        print(f"✓ Created {chunk_count[0]['CNT']} smart chunks")

    except Exception as e:
        print(f"Error: {e}")


def main():
    session = get_session()

    print("=== Article Enhancement Tool ===\n")

    print("現在のRSSデータを最大限活用する方法：\n")
    print("1. タイトルから関連キーワードを生成")
    print("2. AIで記事内容を推測・拡張")
    print("3. タイトルも検索対象チャンクに含める")
    print("4. 要約から重要な情報を抽出\n")

    choice = input("実行しますか？ (y/n): ")

    if choice.lower() == "y":
        print("\n1. 記事を拡張中...")
        enhance_article_content(session)

        print("\n2. スマートチャンクを作成中...")
        create_smart_chunks(session)

        print("\n✓ 完了！Streamlit UIで埋め込みを生成してください。")
    else:
        print("\n代替案：")
        print("- 現在の要約データでそのまま進める")
        print("- 手動で記事全文をCSV/JSONでアップロード")
        print("- 別のブログサービス（はてなブログ等）のRSSを使用")
        print("- note APIの利用可能性を調査")

    session.close()


if __name__ == "__main__":
    main()
