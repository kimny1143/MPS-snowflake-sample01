-- ========================================
-- MUED Snowflake AI App - Database Setup
-- ========================================

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS MUED;
USE DATABASE MUED;

-- Create schema if not exists
CREATE SCHEMA IF NOT EXISTS PUBLIC;
USE SCHEMA PUBLIC;

-- ========================================
-- Stage for RSS data
-- ========================================
CREATE STAGE IF NOT EXISTS RSS_STAGE
    DIRECTORY = (ENABLE = TRUE)
    COMMENT = 'Stage for RSS XML files';

-- ========================================
-- Raw layer: Store raw XML data
-- ========================================
CREATE TABLE IF NOT EXISTS BLOG_POSTS_RAW (
    xml VARIANT,
    fetched_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _metadata VARIANT DEFAULT OBJECT_CONSTRUCT(
        'source_url', CURRENT_USER(),
        'load_timestamp', CURRENT_TIMESTAMP()::STRING
    )
) COMMENT = 'Raw RSS XML data storage';

-- ========================================
-- Core layer: Parsed and enriched blog posts
-- ========================================
CREATE TABLE IF NOT EXISTS BLOG_POSTS (
    id VARCHAR(255) PRIMARY KEY,
    title VARCHAR(1000) NOT NULL,
    body_markdown TEXT,
    level VARCHAR(50),
    tags ARRAY,
    summary VARCHAR(2000),
    emb VECTOR(FLOAT, 768),
    url VARCHAR(1000),
    published_at TIMESTAMP_NTZ,
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
) COMMENT = 'Parsed and enriched blog posts with embeddings';

-- Create index on embeddings for vector search
-- Note: This syntax may vary based on Snowflake version
-- CREATE VECTOR INDEX IF NOT EXISTS idx_blog_posts_emb ON BLOG_POSTS(emb);

-- ========================================
-- Stream for change data capture
-- ========================================
CREATE STREAM IF NOT EXISTS BLOG_POSTS_RAW_STREAM
    ON TABLE BLOG_POSTS_RAW
    COMMENT = 'Captures changes in raw RSS data';

-- ========================================
-- Warehouse for compute
-- ========================================
CREATE WAREHOUSE IF NOT EXISTS COMPUTE_WH
    WITH WAREHOUSE_SIZE = 'XSMALL'
    WAREHOUSE_TYPE = 'STANDARD'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    MIN_CLUSTER_COUNT = 1
    MAX_CLUSTER_COUNT = 1
    SCALING_POLICY = 'STANDARD'
    COMMENT = 'Warehouse for RSS processing and vector operations';

-- ========================================
-- Grant permissions (adjust as needed)
-- ========================================
GRANT USAGE ON DATABASE MUED TO ROLE PUBLIC;
GRANT USAGE ON SCHEMA PUBLIC TO ROLE PUBLIC;
GRANT ALL ON STAGE RSS_STAGE TO ROLE PUBLIC;
GRANT ALL ON TABLE BLOG_POSTS_RAW TO ROLE PUBLIC;
GRANT ALL ON TABLE BLOG_POSTS TO ROLE PUBLIC;
GRANT ALL ON STREAM BLOG_POSTS_RAW_STREAM TO ROLE PUBLIC;

-- ========================================
-- Validation queries
-- ========================================
-- Check if tables exist
SHOW TABLES;

-- Check if stage exists
SHOW STAGES;

-- Check if stream exists
SHOW STREAMS;
