-- ========================================
-- Create Snowflake TASK for automated transformation
-- ========================================

USE DATABASE MUED;
USE SCHEMA PUBLIC;
USE WAREHOUSE COMPUTE_WH;

-- Create stored procedure for transformation
CREATE OR REPLACE PROCEDURE TRANSFORM_BLOG_POSTS()
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS OWNER
AS
$$
DECLARE
    result_message VARCHAR;
    row_count INTEGER;
BEGIN
    -- Execute the transformation
    EXECUTE IMMEDIATE FROM './src/transform.sql';

    -- Get row count
    SELECT COUNT(*) INTO :row_count FROM BLOG_POSTS_RAW_STREAM;

    -- Set result message
    result_message := 'Processed ' || :row_count || ' records at ' || CURRENT_TIMESTAMP()::VARCHAR;

    RETURN result_message;
EXCEPTION
    WHEN OTHER THEN
        RETURN 'Error: ' || SQLERRM;
END;
$$;

-- Create task to run transformation every 5 minutes
CREATE OR REPLACE TASK TRANSFORM_BLOG_POSTS_TASK
    WAREHOUSE = COMPUTE_WH
    SCHEDULE = '5 MINUTE'
    WHEN SYSTEM$STREAM_HAS_DATA('BLOG_POSTS_RAW_STREAM')
AS
    CALL TRANSFORM_BLOG_POSTS();

-- Enable the task
ALTER TASK TRANSFORM_BLOG_POSTS_TASK RESUME;

-- Show task status
SHOW TASKS;

-- Monitor task execution history (run this to check)
-- SELECT *
-- FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(
--     SCHEDULED_TIME_RANGE_START => DATEADD('hour', -24, CURRENT_TIMESTAMP()),
--     TASK_NAME => 'TRANSFORM_BLOG_POSTS_TASK'
-- ))
-- ORDER BY SCHEDULED_TIME DESC;
