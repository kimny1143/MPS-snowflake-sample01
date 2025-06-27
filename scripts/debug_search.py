#!/usr/bin/env python
"""Debug semantic search"""

import sys

sys.path.insert(0, ".")


from src.config import get_session


def main():
    session = get_session()

    try:
        print("Debugging semantic search...")

        session.sql("USE DATABASE MUED").collect()

        # 1. Check function
        print("\n1. Checking cosine similarity function...")
        try:
            result = session.sql(
                "SHOW FUNCTIONS LIKE '%COSINE%' IN SCHEMA STG"
            ).collect()
            for r in result:
                print(f"  Function: {r[1]}")
        except Exception as e:
            print(f"  Error: {e}")

        # 2. Test function directly
        print("\n2. Testing function with sample vectors...")
        try:
            test = session.sql(
                """
                SELECT STG.COSINE_SIMILARITY(
                    [1.0, 2.0, 3.0]::ARRAY,
                    [1.0, 2.0, 3.0]::ARRAY
                ) as similarity
            """
            ).collect()
            print(f"  Result: {test[0]['SIMILARITY']}")
        except Exception as e:
            print(f"  Error: {e}")

        # 3. Check embeddings
        print("\n3. Checking embeddings...")
        try:
            sample = session.sql(
                """
                SELECT
                    CHUNK_ID,
                    ARRAY_SIZE(EMBEDDING_VECTOR) as vector_size
                FROM STG.ARTICLE_EMBEDDINGS
                LIMIT 5
            """
            ).collect()
            for s in sample:
                print(f"  Chunk {s['CHUNK_ID']}: {s['VECTOR_SIZE']} dimensions")
        except Exception as e:
            print(f"  Error: {e}")

        # 4. Test simple search without function
        print("\n4. Testing simple search...")
        try:
            result = session.sql(
                """
                SELECT
                    ARTICLE_ID,
                    TITLE,
                    CHUNK_TEXT
                FROM STG.ARTICLE_SEARCH
                LIMIT 3
            """
            ).collect()
            print(f"  Found {len(result)} articles")
        except Exception as e:
            print(f"  Error: {e}")

        session.close()

    except Exception as e:
        print(f"Error: {e}")
        session.close()


if __name__ == "__main__":
    main()
