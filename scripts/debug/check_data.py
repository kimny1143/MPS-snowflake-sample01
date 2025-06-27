#!/usr/bin/env python
"""Check data in tables"""

import sys

sys.path.insert(0, ".")

from src.config import get_session


def main():
    session = get_session()

    try:
        session.sql("USE DATABASE MUED").collect()

        print("=== Data Check ===\n")

        # 1. Check chunks
        print("1. Chunks in STG.ARTICLE_CHUNKS:")
        chunks = session.sql(
            """
            SELECT
                CHUNK_ID,
                ARTICLE_URL,
                SUBSTRING(CHUNK_TEXT, 1, 100) as CHUNK_PREVIEW,
                CHUNK_LENGTH
            FROM STG.ARTICLE_CHUNKS
            ORDER BY CHUNK_LENGTH DESC
            LIMIT 5
        """
        ).collect()
        for c in chunks:
            print(
                f"  - {c['CHUNK_ID']}: {c['CHUNK_PREVIEW']}... ({c['CHUNK_LENGTH']} chars)"
            )

        # 2. Check for 'マイク' in chunks
        print("\n2. Searching for 'マイク' in chunks:")
        try:
            mic_chunks = session.sql(
                """
                SELECT COUNT(*) as count
                FROM STG.ARTICLE_CHUNKS
                WHERE LOWER(CHUNK_TEXT) LIKE '%マイク%'
                   OR LOWER(CHUNK_TEXT) LIKE '%mic%'
                   OR LOWER(CHUNK_TEXT) LIKE '%microphone%'
            """
            ).collect()
            print(f"  Found: {mic_chunks[0]['COUNT']} chunks")
        except Exception as e:
            print(f"  Error searching: {e}")

        # 3. Check embeddings
        print("\n3. Embeddings status:")
        emb_status = session.sql(
            """
            SELECT
                COUNT(DISTINCT c.CHUNK_ID) as total_chunks,
                COUNT(DISTINCT e.CHUNK_ID) as chunks_with_embeddings,
                COUNT(*) as total_embeddings
            FROM STG.ARTICLE_CHUNKS c
            LEFT JOIN STG.ARTICLE_EMBEDDINGS e ON c.CHUNK_ID = e.CHUNK_ID
        """
        ).collect()
        print(f"  Total chunks: {emb_status[0]['TOTAL_CHUNKS']}")
        print(f"  Chunks with embeddings: {emb_status[0]['CHUNKS_WITH_EMBEDDINGS']}")

        # 4. Check article titles
        print("\n4. Article titles in CORE.BLOG_POSTS:")
        titles = session.sql(
            """
            SELECT TITLE
            FROM CORE.BLOG_POSTS
            ORDER BY PUBLISHED_AT DESC
            LIMIT 10
        """
        ).collect()
        for t in titles:
            print(f"  - {t['TITLE']}")

        # 5. Check RAW data
        print("\n5. RAW RSS data check:")
        raw_count = session.sql(
            "SELECT COUNT(*) as cnt FROM RAW.NOTE_RSS_RAW"
        ).collect()
        print(f"  RAW records: {raw_count[0]['CNT']}")

        # Check if RAW data contains multiple articles
        raw_sample = session.sql(
            """
            SELECT
                RAW_DATA,
                ARRAY_SIZE(RAW_DATA) as article_count
            FROM RAW.NOTE_RSS_RAW
            LIMIT 1
        """
        ).collect()
        if raw_sample:
            print(f"  Articles in RAW data: {raw_sample[0]['ARTICLE_COUNT']}")

        # 6. Check if chunks are properly created
        print("\n6. Sample article body:")
        sample = session.sql(
            """
            SELECT
                TITLE,
                SUBSTRING(BODY, 1, 500) as BODY_PREVIEW
            FROM CORE.BLOG_POSTS
            WHERE BODY LIKE '%マイク%'
               OR BODY LIKE '%レコーディング%'
               OR BODY LIKE '%音楽%'
            LIMIT 3
        """
        ).collect()
        for s in sample:
            print(f"\n  Title: {s['TITLE']}")
            print(f"  Body: {s['BODY_PREVIEW']}...")

        session.close()

    except Exception as e:
        print(f"Error: {e}")
        session.close()


if __name__ == "__main__":
    main()
