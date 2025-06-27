#!/usr/bin/env python
"""Create article chunks procedure"""

import sys

sys.path.insert(0, ".")

from src.config import get_session


def main():
    session = get_session()

    try:
        print("Creating chunks procedure...")

        session.sql("USE DATABASE MUED").collect()

        # Create procedure to chunk articles
        session.sql(
            """
            CREATE OR REPLACE PROCEDURE STG.CREATE_ARTICLE_CHUNKS()
            RETURNS VARCHAR
            LANGUAGE SQL
            AS
            $$
            BEGIN
                -- Clear existing chunks
                DELETE FROM STG.ARTICLE_CHUNKS
                WHERE ARTICLE_URL IN (SELECT URL FROM CORE.BLOG_POSTS);

                -- Create new chunks (simple version: split by paragraphs)
                INSERT INTO STG.ARTICLE_CHUNKS (ARTICLE_ID, ARTICLE_URL, CHUNK_INDEX, CHUNK_TEXT, CHUNK_LENGTH)
                SELECT
                    ID as ARTICLE_ID,
                    URL as ARTICLE_URL,
                    SEQ4() as CHUNK_INDEX,
                    TRIM(value) as CHUNK_TEXT,
                    LENGTH(TRIM(value)) as CHUNK_LENGTH
                FROM CORE.BLOG_POSTS,
                LATERAL SPLIT_TO_TABLE(BODY, '\n\n')
                WHERE LENGTH(TRIM(value)) > 100;  -- Minimum chunk size

                RETURN 'Created ' || SQLROWCOUNT || ' chunks';
            END;
            $$
        """
        ).collect()

        print("✓ Chunks procedure created successfully!")

        # Test by creating chunks
        result = session.sql("CALL STG.CREATE_ARTICLE_CHUNKS()").collect()
        print(f"Test result: {result[0][0]}")

        session.close()

    except Exception as e:
        print(f"Error: {e}")
        session.close()


if __name__ == "__main__":
    main()
