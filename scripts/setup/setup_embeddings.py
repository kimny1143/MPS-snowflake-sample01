#!/usr/bin/env python
"""Setup Snowflake embeddings tables"""

import sys

sys.path.insert(0, ".")

from src.config import get_session


def main():
    session = get_session()

    try:
        print("Setting up embeddings tables...")

        # Ensure we're using the right database
        session.sql("USE DATABASE MUED").collect()

        # Create chunks table
        print("Creating ARTICLE_CHUNKS table...")
        session.sql(
            """
            CREATE OR REPLACE TABLE STG.ARTICLE_CHUNKS (
                CHUNK_ID VARCHAR(36) PRIMARY KEY DEFAULT UUID_STRING(),
                ARTICLE_ID VARCHAR(36),
                ARTICLE_URL VARCHAR(500),
                CHUNK_INDEX INTEGER,
                CHUNK_TEXT TEXT,
                CHUNK_LENGTH INTEGER,
                CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
                FOREIGN KEY (ARTICLE_URL) REFERENCES CORE.BLOG_POSTS(URL)
            )
        """
        ).collect()

        # Create embeddings table
        print("Creating ARTICLE_EMBEDDINGS table...")
        session.sql(
            """
            CREATE OR REPLACE TABLE STG.ARTICLE_EMBEDDINGS (
                EMBEDDING_ID VARCHAR(36) PRIMARY KEY DEFAULT UUID_STRING(),
                CHUNK_ID VARCHAR(36),
                EMBEDDING_VECTOR ARRAY,
                MODEL_NAME VARCHAR(100),
                CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
                FOREIGN KEY (CHUNK_ID) REFERENCES STG.ARTICLE_CHUNKS(CHUNK_ID)
            )
        """
        ).collect()

        # Create cosine similarity function
        print("Creating cosine similarity function...")
        session.sql(
            """
            CREATE OR REPLACE FUNCTION STG.COSINE_SIMILARITY(v1 ARRAY, v2 ARRAY)
            RETURNS FLOAT
            LANGUAGE SQL
            AS $$
                SELECT
                    CASE
                        WHEN ARRAY_SIZE(v1) != ARRAY_SIZE(v2) THEN NULL
                        WHEN ARRAY_SIZE(v1) = 0 THEN NULL
                        ELSE
                            SUM(v1[i] * v2[i]) /
                            (SQRT(SUM(v1[i] * v1[i])) * SQRT(SUM(v2[i] * v2[i])))
                    END
                FROM (
                    SELECT SEQ4() as i
                    FROM TABLE(GENERATOR(ROWCOUNT => ARRAY_SIZE(v1)))
                )
            $$
        """
        ).collect()

        # Create search view
        print("Creating search view...")
        session.sql(
            """
            CREATE OR REPLACE VIEW STG.ARTICLE_SEARCH AS
            SELECT
                c.CHUNK_ID,
                c.ARTICLE_ID,
                c.ARTICLE_URL,
                c.CHUNK_INDEX,
                c.CHUNK_TEXT,
                p.TITLE,
                p.PUBLISHED_AT,
                e.EMBEDDING_VECTOR,
                e.MODEL_NAME
            FROM STG.ARTICLE_CHUNKS c
            JOIN STG.ARTICLE_EMBEDDINGS e ON c.CHUNK_ID = e.CHUNK_ID
            JOIN CORE.BLOG_POSTS p ON c.ARTICLE_URL = p.URL
        """
        ).collect()

        print("✓ Embeddings tables created successfully!")

        # Check what was created
        tables = session.sql("SHOW TABLES IN SCHEMA STG").collect()
        print(f"\nSTG tables created: {len(tables)}")
        for t in tables:
            print(f"  - {t[1]}")

        session.close()

    except Exception as e:
        print(f"Error: {e}")
        session.close()


if __name__ == "__main__":
    main()
