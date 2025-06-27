#!/usr/bin/env python
"""Check actual article content"""

import sys

sys.path.insert(0, ".")

from src.config import get_session


def main():
    session = get_session()

    try:
        print("Checking article content...")

        session.sql("USE DATABASE MUED").collect()

        # Check article bodies
        print("\n1. Article body lengths:")
        bodies = session.sql(
            """
            SELECT
                TITLE,
                URL,
                LENGTH(BODY) as body_length,
                SUBSTRING(BODY, 1, 200) as body_preview
            FROM CORE.BLOG_POSTS
            ORDER BY body_length DESC
            LIMIT 5
        """
        ).collect()

        for b in bodies:
            print(f"\n  Title: {b['TITLE']}")
            print(f"  URL: {b['URL']}")
            print(f"  Length: {b['BODY_LENGTH']} chars")
            print(f"  Preview: {b['BODY_PREVIEW']}...")

        # Check if bodies contain full content
        print("\n2. Checking for keywords in article bodies:")
        keywords = [
            "マイク",
            "レコーディング",
            "音楽",
            "作曲",
            "DTM",
            "DAW",
            "ミックス",
            "マスタリング",
        ]

        for keyword in keywords:
            count = session.sql(
                f"""
                SELECT COUNT(*) as cnt
                FROM CORE.BLOG_POSTS
                WHERE BODY LIKE '%{keyword}%'
            """
            ).collect()
            print(f"  '{keyword}': {count[0]['CNT']} articles")

        # Check RAW data structure
        print("\n3. RAW data structure:")
        raw_sample = session.sql(
            """
            SELECT
                f.value:title::VARCHAR as title,
                f.value:url::VARCHAR as url,
                LENGTH(f.value:body::VARCHAR) as body_length,
                SUBSTRING(f.value:body::VARCHAR, 1, 200) as body_preview
            FROM RAW.NOTE_RSS_RAW r,
            LATERAL FLATTEN(input => r.RAW_DATA) f
            LIMIT 3
        """
        ).collect()

        for s in raw_sample:
            print(f"\n  RAW Title: {s['TITLE']}")
            print(f"  RAW Body Length: {s['BODY_LENGTH']}")
            print(f"  RAW Body Preview: {s['BODY_PREVIEW']}...")

        session.close()

    except Exception as e:
        print(f"Error: {e}")
        session.close()


if __name__ == "__main__":
    main()
