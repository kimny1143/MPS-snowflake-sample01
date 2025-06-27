#!/usr/bin/env python
"""Recreate all chunks for all articles"""

import sys

sys.path.insert(0, ".")

from src.config import get_session


def main():
    session = get_session()

    try:
        print("Recreating chunks for all articles...")

        session.sql("USE DATABASE MUED").collect()

        # First, clear existing chunks
        print("1. Clearing existing chunks...")
        session.sql("DELETE FROM STG.ARTICLE_EMBEDDINGS").collect()
        session.sql("DELETE FROM STG.ARTICLE_CHUNKS").collect()

        # Create chunks for all articles
        print("2. Creating chunks for all articles...")
        result = session.sql(
            """
            INSERT INTO STG.ARTICLE_CHUNKS (ARTICLE_ID, ARTICLE_URL, CHUNK_INDEX, CHUNK_TEXT, CHUNK_LENGTH)
            WITH split_articles AS (
                SELECT
                    ID as ARTICLE_ID,
                    URL as ARTICLE_URL,
                    value as CHUNK_TEXT,
                    SEQ4() as CHUNK_INDEX
                FROM CORE.BLOG_POSTS,
                LATERAL SPLIT_TO_TABLE(BODY, '\n\n')
                WHERE LENGTH(TRIM(value)) > 50  -- Minimum chunk size
            )
            SELECT
                ARTICLE_ID,
                ARTICLE_URL,
                CHUNK_INDEX,
                CHUNK_TEXT,
                LENGTH(CHUNK_TEXT) as CHUNK_LENGTH
            FROM split_articles
        """
        ).collect()

        # Count results
        chunk_count = session.sql(
            "SELECT COUNT(*) as cnt FROM STG.ARTICLE_CHUNKS"
        ).collect()
        article_count = session.sql(
            "SELECT COUNT(DISTINCT ARTICLE_URL) as cnt FROM STG.ARTICLE_CHUNKS"
        ).collect()

        print(
            f"\n✓ Created {chunk_count[0]['CNT']} chunks from {article_count[0]['CNT']} articles"
        )

        # Show sample chunks
        print("\n3. Sample chunks:")
        samples = session.sql(
            """
            SELECT
                ARTICLE_URL,
                COUNT(*) as chunk_count,
                MAX(CHUNK_LENGTH) as max_length
            FROM STG.ARTICLE_CHUNKS
            GROUP BY ARTICLE_URL
            ORDER BY chunk_count DESC
            LIMIT 5
        """
        ).collect()

        for s in samples:
            print(
                f"  - {s['ARTICLE_URL']}: {s['CHUNK_COUNT']} chunks (max {s['MAX_LENGTH']} chars)"
            )

        # Search for マイク
        print("\n4. Searching for 'マイク' in chunks:")
        mic_results = session.sql(
            """
            SELECT
                c.ARTICLE_URL,
                p.TITLE,
                COUNT(*) as match_count
            FROM STG.ARTICLE_CHUNKS c
            JOIN CORE.BLOG_POSTS p ON c.ARTICLE_URL = p.URL
            WHERE c.CHUNK_TEXT LIKE '%マイク%'
               OR c.CHUNK_TEXT LIKE '%mic%'
               OR c.CHUNK_TEXT LIKE '%レコーディング%'
            GROUP BY c.ARTICLE_URL, p.TITLE
        """
        ).collect()

        if mic_results:
            print(f"  Found {len(mic_results)} articles with relevant content:")
            for m in mic_results:
                print(f"    - {m['TITLE']}: {m['MATCH_COUNT']} matching chunks")
        else:
            print("  No matches found")

        session.close()

    except Exception as e:
        print(f"Error: {e}")
        session.close()


if __name__ == "__main__":
    main()
