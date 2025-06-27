#!/usr/bin/env python
"""Setup Snowflake tables and procedures"""

import sys

sys.path.insert(0, ".")

from src.config import get_session


def main():
    session = get_session()

    try:
        print("Setting up tables and procedures...")

        # Ensure we're using the right database
        session.sql("USE DATABASE MUED").collect()

        # Create file format
        print("Creating file format...")
        session.sql(
            """
            CREATE OR REPLACE FILE FORMAT RAW.JSON_FORMAT
                TYPE = 'JSON'
                COMPRESSION = 'AUTO'
                STRIP_OUTER_ARRAY = TRUE
        """
        ).collect()

        # Create stage
        print("Creating stage...")
        session.sql(
            """
            CREATE OR REPLACE STAGE RAW.RSS_STAGE
                FILE_FORMAT = RAW.JSON_FORMAT
        """
        ).collect()

        # Create RAW table
        print("Creating RAW table...")
        session.sql(
            """
            CREATE OR REPLACE TABLE RAW.NOTE_RSS_RAW (
                ID VARCHAR(36) DEFAULT UUID_STRING(),
                SOURCE_URL VARCHAR(500),
                FETCHED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
                RAW_DATA VARIANT,
                PRIMARY KEY (ID)
            )
        """
        ).collect()

        # Create STG view
        print("Creating STG view...")
        session.sql(
            """
            CREATE OR REPLACE VIEW STG.NOTE_ARTICLES AS
            SELECT
                r.ID as RAW_ID,
                r.SOURCE_URL,
                r.FETCHED_AT,
                f.value:id::VARCHAR as ARTICLE_ID,
                f.value:title::VARCHAR as TITLE,
                f.value:url::VARCHAR as URL,
                TRY_TO_TIMESTAMP_NTZ(f.value:published_at::VARCHAR) as PUBLISHED_AT,
                f.value:body::VARCHAR as BODY,
                LENGTH(f.value:body::VARCHAR) as BODY_LENGTH
            FROM RAW.NOTE_RSS_RAW r,
            LATERAL FLATTEN(input => r.RAW_DATA) f
        """
        ).collect()

        # Create CORE table
        print("Creating CORE table...")
        session.sql(
            """
            CREATE OR REPLACE TABLE CORE.BLOG_POSTS (
                ID VARCHAR(36) PRIMARY KEY,
                TITLE VARCHAR(500),
                URL VARCHAR(500) UNIQUE,
                PUBLISHED_AT TIMESTAMP_NTZ,
                BODY TEXT,
                BODY_LENGTH INTEGER,
                FIRST_FETCHED_AT TIMESTAMP_NTZ,
                LAST_UPDATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
            )
        """
        ).collect()

        # Create stream on RAW table instead of view
        print("Creating stream on RAW table...")
        session.sql(
            """
            CREATE OR REPLACE STREAM RAW.NOTE_RSS_RAW_STREAM ON TABLE RAW.NOTE_RSS_RAW
                APPEND_ONLY = TRUE
        """
        ).collect()

        # Create merge procedure
        print("Creating merge procedure...")
        session.sql(
            """
            CREATE OR REPLACE PROCEDURE CORE.MERGE_BLOG_POSTS()
            RETURNS VARCHAR
            LANGUAGE SQL
            AS
            $$
            BEGIN
                MERGE INTO CORE.BLOG_POSTS t
                USING (
                    SELECT
                        f.value:id::VARCHAR as ARTICLE_ID,
                        f.value:title::VARCHAR as TITLE,
                        f.value:url::VARCHAR as URL,
                        TRY_TO_TIMESTAMP_NTZ(f.value:published_at::VARCHAR) as PUBLISHED_AT,
                        f.value:body::VARCHAR as BODY,
                        LENGTH(f.value:body::VARCHAR) as BODY_LENGTH,
                        MIN(r.FETCHED_AT) as FIRST_FETCHED_AT
                    FROM RAW.NOTE_RSS_RAW_STREAM r,
                    LATERAL FLATTEN(input => r.RAW_DATA) f
                    WHERE r.METADATA$ACTION = 'INSERT'
                    GROUP BY ARTICLE_ID, TITLE, URL, PUBLISHED_AT, BODY, BODY_LENGTH
                ) s
                ON t.URL = s.URL
                WHEN MATCHED AND (t.TITLE != s.TITLE OR t.BODY != s.BODY) THEN
                    UPDATE SET
                        TITLE = s.TITLE,
                        BODY = s.BODY,
                        BODY_LENGTH = s.BODY_LENGTH,
                        LAST_UPDATED_AT = CURRENT_TIMESTAMP()
                WHEN NOT MATCHED THEN
                    INSERT (ID, TITLE, URL, PUBLISHED_AT, BODY, BODY_LENGTH, FIRST_FETCHED_AT)
                    VALUES (s.ARTICLE_ID, s.TITLE, s.URL, s.PUBLISHED_AT, s.BODY, s.BODY_LENGTH, s.FIRST_FETCHED_AT);

                RETURN 'Merge completed: ' || SQLROWCOUNT || ' rows affected';
            END;
            $$
        """
        ).collect()

        # Create task
        print("Creating task...")
        session.sql(
            """
            CREATE OR REPLACE TASK CORE.MERGE_BLOG_POSTS_TASK
                WAREHOUSE = COMPUTE_WH
                SCHEDULE = '5 MINUTE'
                WHEN SYSTEM$STREAM_HAS_DATA('RAW.NOTE_RSS_RAW_STREAM')
            AS
                CALL CORE.MERGE_BLOG_POSTS()
        """
        ).collect()

        print("✓ All tables and procedures created successfully!")

        # Check what was created
        tables = session.sql("SHOW TABLES IN DATABASE MUED").collect()
        print(f"\nTables created: {len(tables)}")
        for t in tables:
            print(f"  - {t[1]}.{t[2]}")

        session.close()

    except Exception as e:
        print(f"Error: {e}")
        session.close()


if __name__ == "__main__":
    main()
