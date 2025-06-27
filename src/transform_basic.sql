-- ========================================
-- Transform SQL - Parse XML (WITHOUT Cortex)
-- ========================================
-- Use this version when Cortex is not available in your Snowflake account
-- This SQL is executed by a Snowflake TASK to process raw RSS data

USE DATABASE MUED;
USE SCHEMA PUBLIC;
USE WAREHOUSE COMPUTE_WH;

-- Transform raw XML to structured blog posts WITHOUT AI enrichment
MERGE INTO BLOG_POSTS AS target
USING (
    WITH channel_data AS (
        SELECT
            XMLGET(xml, 'channel') as channel,
            fetched_at
        FROM BLOG_POSTS_RAW
        WHERE fetched_at >= DATEADD('hour', -24, CURRENT_TIMESTAMP())
    ),
    indices AS (
        SELECT SEQ4() as idx
        FROM TABLE(GENERATOR(ROWCOUNT => 50))
    ),
    parsed_articles AS (
        SELECT
            -- Generate ID from URL or use MD5 hash
            MD5(XMLGET(XMLGET(channel, 'item', idx), 'link'):"$"::VARCHAR) AS id,

            -- Extract basic fields
            XMLGET(XMLGET(channel, 'item', idx), 'title'):"$"::VARCHAR AS title,
            XMLGET(XMLGET(channel, 'item', idx), 'description'):"$"::VARCHAR AS body_markdown,

            -- Default values for fields that would be AI-generated
            'free' AS level,
            ARRAY_CONSTRUCT('note.com', 'rss') AS tags,

            -- URL
            XMLGET(XMLGET(channel, 'item', idx), 'link'):"$"::VARCHAR AS url,

            -- Published date
            TRY_TO_TIMESTAMP_NTZ(
                XMLGET(XMLGET(channel, 'item', idx), 'pubDate'):"$"::VARCHAR,
                'DY, DD MON YYYY HH24:MI:SS'
            ) AS published_at,

            fetched_at

        FROM channel_data, indices
        WHERE XMLGET(channel, 'item', idx) IS NOT NULL
    )
    SELECT
        id,
        title,
        body_markdown,
        level,
        tags,
        -- Simple summary: just use first 200 characters of description
        LEFT(body_markdown, 200) || '...' AS summary,
        NULL AS emb,  -- No embeddings without Cortex
        url,
        published_at,
        CURRENT_TIMESTAMP() AS created_at,
        CURRENT_TIMESTAMP() AS updated_at
    FROM parsed_articles
    WHERE title IS NOT NULL
    QUALIFY ROW_NUMBER() OVER (PARTITION BY id ORDER BY fetched_at DESC) = 1
) AS source
ON target.id = source.id
WHEN MATCHED THEN
    UPDATE SET
        target.title = source.title,
        target.body_markdown = source.body_markdown,
        target.level = source.level,
        target.tags = source.tags,
        target.summary = source.summary,
        target.emb = source.emb,
        target.url = source.url,
        target.published_at = source.published_at,
        target.updated_at = source.updated_at
WHEN NOT MATCHED THEN
    INSERT (
        id, title, body_markdown, level, tags,
        summary, emb, url, published_at, created_at, updated_at
    )
    VALUES (
        source.id, source.title, source.body_markdown, source.level, source.tags,
        source.summary, source.emb, source.url, source.published_at,
        source.created_at, source.updated_at
    );

-- Log transformation results
SELECT
    'Transform completed (Basic version - no Cortex)' AS status,
    COUNT(*) AS records_processed,
    CURRENT_TIMESTAMP() AS processed_at
FROM BLOG_POSTS
WHERE updated_at >= DATEADD('minute', -5, CURRENT_TIMESTAMP());
