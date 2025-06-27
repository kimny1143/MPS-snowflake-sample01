-- ========================================
-- Transform SQL - Parse XML and enrich with Cortex
-- ========================================
-- This SQL is executed by a Snowflake TASK to process raw RSS data

USE DATABASE MUED;
USE SCHEMA PUBLIC;
USE WAREHOUSE COMPUTE_WH;

-- Transform raw XML to structured blog posts with AI enrichment
MERGE INTO BLOG_POSTS AS target
USING (
    WITH parsed_articles AS (
        -- Parse XML/JSON structure from note.com API
        SELECT
            -- Extract article ID
            COALESCE(
                article.value:key::VARCHAR,
                article.value:id::VARCHAR,
                MD5(article.value:name::VARCHAR || article.value:publishedAt::VARCHAR)
            ) AS id,

            -- Extract basic fields
            article.value:name::VARCHAR AS title,
            article.value:body::VARCHAR AS body_markdown,

            -- Extract metadata
            CASE
                WHEN article.value:price::INT > 0 THEN 'premium'
                WHEN article.value:isMembership::BOOLEAN THEN 'membership'
                ELSE 'free'
            END AS level,

            -- Extract tags/hashtags as array
            ARRAY_CONSTRUCT(
                article.value:hashtag::VARCHAR,
                'note.com',
                SPLIT_PART(article.value:user:urlname::VARCHAR, '/', 1)
            ) AS tags,

            -- URL construction
            CONCAT('https://note.com/',
                   article.value:user:urlname::VARCHAR, '/n/',
                   article.value:key::VARCHAR) AS url,

            -- Published date
            TO_TIMESTAMP_NTZ(article.value:publishedAt::VARCHAR) AS published_at,

            -- Track source
            raw.fetched_at,
            raw._metadata

        FROM BLOG_POSTS_RAW raw,
        LATERAL FLATTEN(input => raw.xml:data:contents) article
        WHERE raw.fetched_at >= DATEADD('hour', -24, CURRENT_TIMESTAMP())
          AND article.value:type::VARCHAR = 'TextNote'
    ),
    enriched_articles AS (
        SELECT
            id,
            title,
            body_markdown,
            level,
            tags,
            url,
            published_at,
            fetched_at,

            -- Generate summary using Cortex LLM
            SNOWFLAKE.CORTEX.COMPLETE(
                'mistral-large',
                CONCAT(
                    'Summarize this blog post in 2-3 sentences in Japanese. ',
                    'Focus on the main topic and key takeaways:\n\n',
                    'Title: ', title, '\n\n',
                    'Content: ', LEFT(body_markdown, 2000)
                )
            ) AS summary,

            -- Generate embedding vector using Cortex
            SNOWFLAKE.CORTEX.EMBED_TEXT_768(
                'e5-base-v2',
                CONCAT(title, ' ', COALESCE(LEFT(body_markdown, 1000), ''))
            ) AS emb

        FROM parsed_articles
        WHERE title IS NOT NULL
          AND LENGTH(TRIM(body_markdown)) > 0
    )
    SELECT
        id,
        title,
        body_markdown,
        level,
        tags,
        summary,
        emb,
        url,
        published_at,
        CURRENT_TIMESTAMP() AS created_at,
        CURRENT_TIMESTAMP() AS updated_at
    FROM enriched_articles
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

-- Clean up processed records from stream
CREATE OR REPLACE TEMPORARY TABLE processed_stream_records AS
SELECT * FROM BLOG_POSTS_RAW_STREAM;

-- Log transformation results
SELECT
    'Transform completed' AS status,
    COUNT(*) AS records_processed,
    CURRENT_TIMESTAMP() AS processed_at
FROM processed_stream_records;
