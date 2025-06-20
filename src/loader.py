import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from snowflake.snowpark import Session

from .config import get_session
from .fetch_rss import fetch


def upload_to_stage(session: Session, data: list, stage_name: str = "RAW.RSS_STAGE") -> str:
    """Upload JSON data to Snowflake internal stage"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        temp_path = f.name
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stage_file_name = f"rss_data_{timestamp}.json"
        
        session.file.put(
            local_file_name=temp_path,
            stage_location=f"@{stage_name}",
            dest_file_name=stage_file_name,
            auto_compress=False,
            overwrite=True
        )
        
        return stage_file_name
    finally:
        Path(temp_path).unlink(missing_ok=True)


def load_rss_to_raw(session: Session, feed_url: str) -> dict:
    """Load RSS feed to RAW layer with transaction control"""
    try:
        session.sql("BEGIN").collect()
        
        df = fetch(feed_url)
        data = df.to_dict('records')
        
        stage_file_name = upload_to_stage(session, data)
        
        copy_result = session.sql(f"""
            COPY INTO RAW.NOTE_RSS_RAW (SOURCE_URL, RAW_DATA)
            FROM (
                SELECT 
                    '{feed_url}' as SOURCE_URL,
                    $1 as RAW_DATA
                FROM @RAW.RSS_STAGE/{stage_file_name}
            )
            FILE_FORMAT = (TYPE = JSON)
            ON_ERROR = 'CONTINUE'
        """).collect()
        
        session.sql(f"REMOVE @RAW.RSS_STAGE/{stage_file_name}").collect()
        
        session.sql("COMMIT").collect()
        
        rows_loaded = copy_result[0]['rows_loaded'] if copy_result else 0
        
        return {
            "status": "success",
            "feed_url": feed_url,
            "rows_loaded": rows_loaded,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        session.sql("ROLLBACK").collect()
        return {
            "status": "error",
            "feed_url": feed_url,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def execute_merge(session: Session) -> dict:
    """Execute merge from STG to CORE layer"""
    try:
        result = session.sql("CALL CORE.MERGE_BLOG_POSTS()").collect()
        return {
            "status": "success",
            "message": result[0][0] if result else "No rows to merge",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def enable_task(session: Session, task_name: str = "CORE.MERGE_BLOG_POSTS_TASK") -> dict:
    """Enable or resume a Snowflake task"""
    try:
        session.sql(f"ALTER TASK {task_name} RESUME").collect()
        return {
            "status": "success",
            "task": task_name,
            "action": "resumed",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "task": task_name,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def get_task_status(session: Session) -> pd.DataFrame:
    """Get status of all tasks"""
    return session.sql("""
        SHOW TASKS IN DATABASE MUED
    """).to_pandas()