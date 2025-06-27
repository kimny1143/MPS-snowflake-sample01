#!/usr/bin/env python
"""Check view columns"""

import sys

sys.path.insert(0, ".")

from src.config import get_session


def main():
    session = get_session()

    try:
        print("Checking ARTICLE_SEARCH view columns...")

        session.sql("USE DATABASE MUED").collect()

        # Check if view exists and get columns
        try:
            columns = session.sql("DESCRIBE VIEW STG.ARTICLE_SEARCH").collect()
            print("\nColumns in ARTICLE_SEARCH:")
            for col in columns:
                print(f"  - {col[0]}: {col[1]}")
        except:
            print("ARTICLE_SEARCH view not found")

        # Check actual data
        try:
            sample = session.sql("SELECT * FROM STG.ARTICLE_SEARCH LIMIT 1").collect()
            if sample:
                print("\nSample data columns:")
                for key in sample[0].as_dict().keys():
                    print(f"  - {key}")
            else:
                print("\nNo data in ARTICLE_SEARCH")
        except Exception as e:
            print(f"Error checking data: {e}")

        # Check embeddings table
        try:
            count = session.sql(
                "SELECT COUNT(*) as cnt FROM STG.ARTICLE_EMBEDDINGS"
            ).collect()
            print(f"\nEmbeddings count: {count[0]['CNT']}")
        except:
            print("\nEmbeddings table not found")

        session.close()

    except Exception as e:
        print(f"Error: {e}")
        session.close()


if __name__ == "__main__":
    main()
