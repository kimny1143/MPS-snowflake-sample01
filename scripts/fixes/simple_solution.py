#!/usr/bin/env python
"""Simple solution: Use title + summary effectively"""

import sys

sys.path.insert(0, ".")

from src.config import get_session


def create_title_based_chunks(session):
    """Create chunks that include title for better search"""
    try:
        print("Creating title-based chunks...")

        session.sql("USE DATABASE MUED").collect()

        # チャンクをクリア
        session.sql("DELETE FROM STG.ARTICLE_EMBEDDINGS").collect()
        session.sql("DELETE FROM STG.ARTICLE_CHUNKS").collect()

        # タイトル + 要約を組み合わせたチャンクを作成
        result = session.sql(
            """
            INSERT INTO STG.ARTICLE_CHUNKS (ARTICLE_ID, ARTICLE_URL, CHUNK_INDEX, CHUNK_TEXT, CHUNK_LENGTH)
            SELECT
                ID as ARTICLE_ID,
                URL as ARTICLE_URL,
                1 as CHUNK_INDEX,
                CONCAT(
                    '【タイトル】', TITLE, '\n\n',
                    '【内容】', BODY, '\n\n',
                    '【URL】', URL
                ) as CHUNK_TEXT,
                LENGTH(CONCAT(TITLE, BODY)) as CHUNK_LENGTH
            FROM CORE.BLOG_POSTS
        """
        ).collect()

        # 統計を表示
        stats = session.sql(
            """
            SELECT
                COUNT(*) as total_chunks,
                AVG(CHUNK_LENGTH) as avg_length,
                MAX(CHUNK_LENGTH) as max_length
            FROM STG.ARTICLE_CHUNKS
        """
        ).collect()

        print(f"\n✓ Created {stats[0]['TOTAL_CHUNKS']} chunks")
        print(f"  Average length: {stats[0]['AVG_LENGTH']:.0f} chars")
        print(f"  Max length: {stats[0]['MAX_LENGTH']} chars")

        # サンプル表示
        print("\nSample chunks:")
        samples = session.sql(
            """
            SELECT
                SUBSTRING(CHUNK_TEXT, 1, 200) as preview
            FROM STG.ARTICLE_CHUNKS
            LIMIT 3
        """
        ).collect()

        for i, s in enumerate(samples, 1):
            print(f"\n{i}. {s['PREVIEW']}...")

        print("\n✓ 次はStreamlit UIで「埋め込み生成」を実行してください")

    except Exception as e:
        print(f"Error: {e}")


def check_music_keywords(session):
    """Check if articles contain music-related keywords"""
    print("\n音楽関連キーワードのチェック...")

    keywords = {
        "タイトル検索": [
            "音楽",
            "作曲",
            "レコーディング",
            "DTM",
            "DAW",
            "ミックス",
            "マスタリング",
            "楽曲",
            "サウンド",
        ],
        "本文検索": ["glasswerks", "木村", "note", "制作", "プロジェクト"],
    }

    for search_type, words in keywords.items():
        print(f"\n{search_type}:")
        for keyword in words:
            if search_type == "タイトル検索":
                count = session.sql(
                    f"""
                    SELECT COUNT(*) as cnt
                    FROM CORE.BLOG_POSTS
                    WHERE LOWER(TITLE) LIKE LOWER('%{keyword}%')
                """
                ).collect()
            else:
                count = session.sql(
                    f"""
                    SELECT COUNT(*) as cnt
                    FROM CORE.BLOG_POSTS
                    WHERE LOWER(BODY) LIKE LOWER('%{keyword}%')
                """
                ).collect()

            if count[0]["CNT"] > 0:
                print(f"  ✓ '{keyword}': {count[0]['CNT']} 件")


def main():
    session = get_session()

    print("=== シンプルな解決策 ===\n")
    print("noteのRSS制限を回避する最も簡単な方法：")
    print("タイトルと要約を組み合わせて検索可能にする\n")

    # 音楽関連キーワードをチェック
    check_music_keywords(session)

    print("\n" + "=" * 50)
    print("\nタイトル+要約チャンクを作成しますか？")
    print("これにより、タイトルでの検索が可能になります。")

    choice = input("\n実行する (y/n): ")

    if choice.lower() == "y":
        create_title_based_chunks(session)

    session.close()


if __name__ == "__main__":
    main()
