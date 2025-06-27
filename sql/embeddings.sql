-- Embeddings extension for RAG functionality
USE DATABASE MUED;

-- STG layer: Articles with chunks for embedding
CREATE OR REPLACE TABLE STG.ARTICLE_CHUNKS (
    CHUNK_ID VARCHAR(36) DEFAULT UUID_STRING() PRIMARY KEY,
    ARTICLE_ID VARCHAR(36),
    CHUNK_INDEX INTEGER,
    CHUNK_TEXT TEXT,
    CHUNK_LENGTH INTEGER,
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    FOREIGN KEY (ARTICLE_ID) REFERENCES CORE.BLOG_POSTS(ID)
);

-- STG layer: Store embeddings
CREATE OR REPLACE TABLE STG.ARTICLE_EMBEDDINGS (
    EMBEDDING_ID VARCHAR(36) DEFAULT UUID_STRING() PRIMARY KEY,
    CHUNK_ID VARCHAR(36),
    EMBEDDING_VECTOR ARRAY,
    MODEL_NAME VARCHAR(100) DEFAULT 'text-embedding-3-small',
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    FOREIGN KEY (CHUNK_ID) REFERENCES STG.ARTICLE_CHUNKS(CHUNK_ID)
);

-- Function to split text into chunks
CREATE OR REPLACE FUNCTION STG.SPLIT_TEXT_TO_CHUNKS(
    text VARCHAR,
    chunk_size INTEGER DEFAULT 1000,
    overlap INTEGER DEFAULT 200
)
RETURNS TABLE (chunk_index INTEGER, chunk_text VARCHAR)
LANGUAGE SQL
AS
$$
    WITH RECURSIVE chunks AS (
        SELECT
            0 as chunk_index,
            SUBSTR(text, 1, chunk_size) as chunk_text,
            chunk_size - overlap as next_pos,
            LENGTH(text) as text_length

        UNION ALL

        SELECT
            chunk_index + 1,
            SUBSTR(text, next_pos + 1, chunk_size),
            next_pos + chunk_size - overlap,
            text_length
        FROM chunks
        WHERE next_pos < text_length
    )
    SELECT chunk_index, chunk_text
    FROM chunks
    WHERE chunk_text IS NOT NULL AND LENGTH(chunk_text) > 50
$$;

-- Procedure to create chunks from articles
CREATE OR REPLACE PROCEDURE STG.CREATE_ARTICLE_CHUNKS()
RETURNS VARCHAR
LANGUAGE SQL
AS
$$
DECLARE
    chunks_created INTEGER DEFAULT 0;
BEGIN
    -- Clear existing chunks
    TRUNCATE TABLE STG.ARTICLE_CHUNKS;

    -- Create chunks for all articles
    INSERT INTO STG.ARTICLE_CHUNKS (ARTICLE_ID, CHUNK_INDEX, CHUNK_TEXT, CHUNK_LENGTH)
    SELECT
        bp.ID as ARTICLE_ID,
        c.chunk_index,
        c.chunk_text,
        LENGTH(c.chunk_text) as CHUNK_LENGTH
    FROM CORE.BLOG_POSTS bp,
    TABLE(STG.SPLIT_TEXT_TO_CHUNKS(
        CONCAT(bp.TITLE, '\n\n', bp.BODY),
        1000,  -- chunk size
        200    -- overlap
    )) c;

    SELECT COUNT(*) INTO chunks_created FROM STG.ARTICLE_CHUNKS;

    RETURN 'Created ' || chunks_created || ' chunks';
END;
$$;

-- Function to calculate cosine similarity
CREATE OR REPLACE FUNCTION STG.COSINE_SIMILARITY(vec1 ARRAY, vec2 ARRAY)
RETURNS FLOAT
LANGUAGE JAVASCRIPT
AS
$$
    if (!VEC1 || !VEC2 || VEC1.length !== VEC2.length) return null;

    let dotProduct = 0;
    let norm1 = 0;
    let norm2 = 0;

    for (let i = 0; i < VEC1.length; i++) {
        dotProduct += VEC1[i] * VEC2[i];
        norm1 += VEC1[i] * VEC1[i];
        norm2 += VEC2[i] * VEC2[i];
    }

    norm1 = Math.sqrt(norm1);
    norm2 = Math.sqrt(norm2);

    if (norm1 === 0 || norm2 === 0) return 0;

    return dotProduct / (norm1 * norm2);
$$;

-- View for semantic search
CREATE OR REPLACE VIEW STG.SEARCHABLE_ARTICLES AS
SELECT
    c.CHUNK_ID,
    c.ARTICLE_ID,
    c.CHUNK_INDEX,
    c.CHUNK_TEXT,
    e.EMBEDDING_VECTOR,
    bp.TITLE,
    bp.URL,
    bp.PUBLISHED_AT
FROM STG.ARTICLE_CHUNKS c
JOIN STG.ARTICLE_EMBEDDINGS e ON c.CHUNK_ID = e.CHUNK_ID
JOIN CORE.BLOG_POSTS bp ON c.ARTICLE_ID = bp.ID;
