"""
RSS Feed Ingestion Module

Fetches raw RSS XML and loads it into Snowflake BLOG_POSTS_RAW table.
Integrates functionality from fetch_rss.py and loader.py.
"""

import os
import sys
from datetime import datetime
from io import BytesIO
from typing import Any

import requests
from dotenv import load_dotenv
from snowflake.snowpark import Session
from snowflake.snowpark.exceptions import SnowparkSQLException

from src.config import get_snowflake_session

# Load environment variables
load_dotenv()

# 定数
RSS_FEED_URL = os.getenv(
    "RSS_FEED_URL", "https://note.com/api/v2/creators/mued/contents?kind=note&page=1"
)
STAGE_NAME = "@RSS_STAGE"
TABLE_NAME = "BLOG_POSTS_RAW"


# RSS フィードを取得
def fetch_raw_rss(url: str) -> str:
    """
    Fetch raw RSS/XML content from the specified URL.

    Args:
        url: RSS feed URL

    Returns:
        Raw XML/RSS content as string
    """
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        raise Exception(f"Failed to fetch RSS feed: {str(e)}")


# ステージにアップロード
def upload_to_stage(
    session: Session, xml_content: str, stage_name: str
) -> dict[str, Any]:
    """
    Upload raw XML content to Snowflake stage.

    Args:
        session: Snowflake session
        xml_content: Raw XML content
        stage_name: Target stage name

    Returns:
        Dict with upload status and details
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"rss_feed_{timestamp}.xml"

    try:
        # Create in-memory file
        xml_bytes = xml_content.encode("utf-8")
        file_stream = BytesIO(xml_bytes)

        # Upload to stage
        # 一時ファイルとして保存してからアップロード
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".xml", delete=False
        ) as tmp_file:
            tmp_file.write(xml_content)
            tmp_file_path = tmp_file.name

        # ファイルをステージにアップロード
        put_result = session.file.put(
            tmp_file_path, stage_name, auto_compress=True, overwrite=True
        )

        # 一時ファイルを削除
        os.unlink(tmp_file_path)

        # Get the uploaded file path
        uploaded_files = [row.source for row in put_result]

        return {
            "status": "success",
            "file_name": file_name,
            "stage_path": f"{stage_name}/{file_name}",
            "uploaded_files": uploaded_files,
            "timestamp": timestamp,
        }

    except Exception as e:
        return {"status": "error", "error": str(e), "timestamp": timestamp}


# テーブルにロード
def load_to_table(session: Session, stage_path: str, table_name: str) -> dict[str, Any]:
    """
    Load XML data from stage to BLOG_POSTS_RAW table.

    Args:
        session: Snowflake session
        stage_path: Path to file in stage
        table_name: Target table name

    Returns:
        Dict with load status and details
    """
    try:
        # Start transaction
        session.sql("BEGIN").collect()

        # Create table if not exists
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            xml VARIANT,
            fetched_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
        )
        """
        session.sql(create_table_sql).collect()

        # Copy XML data into table
        copy_sql = f"""
        COPY INTO {table_name} (xml, fetched_at)
        FROM (
            SELECT
                TO_VARIANT(PARSE_XML($1, TRUE)),
                CURRENT_TIMESTAMP()
            FROM {stage_path}
        )
        FILE_FORMAT = (TYPE = 'XML')
        ON_ERROR = 'ABORT_STATEMENT'
        """

        copy_result = session.sql(copy_sql).collect()

        # Commit transaction
        session.sql("COMMIT").collect()

        # Clean up stage file
        session.sql(f"REMOVE {stage_path}").collect()

        return {
            "status": "success",
            "rows_loaded": len(copy_result),
            "table": table_name,
            "timestamp": datetime.now().isoformat(),
        }

    except SnowparkSQLException as e:
        # Rollback on error
        session.sql("ROLLBACK").collect()
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


# メイン関数
def ingest_rss_feed() -> dict[str, Any]:
    """
    Main function to ingest RSS feed into Snowflake.

    Returns:
        Dict with complete ingestion status
    """
    results = {"start_time": datetime.now().isoformat(), "steps": []}

    try:
        # Step 1: Fetch RSS feed
        print(f"Fetching RSS feed from: {RSS_FEED_URL}")
        xml_content = fetch_raw_rss(RSS_FEED_URL)
        results["steps"].append(
            {
                "step": "fetch_rss",
                "status": "success",
                "size_bytes": len(xml_content.encode("utf-8")),
            }
        )

        # Step 2: Get Snowflake session
        print("Connecting to Snowflake...")
        session = get_snowflake_session()
        results["steps"].append({"step": "snowflake_connection", "status": "success"})

        # Step 3: Upload to stage
        print(f"Uploading to stage {STAGE_NAME}...")
        upload_result = upload_to_stage(session, xml_content, STAGE_NAME)
        results["steps"].append({"step": "stage_upload", **upload_result})

        if upload_result["status"] != "success":
            raise Exception(f"Stage upload failed: {upload_result.get('error')}")

        # Step 4: Load to table
        print(f"Loading data to table {TABLE_NAME}...")
        load_result = load_to_table(session, upload_result["stage_path"], TABLE_NAME)
        results["steps"].append({"step": "table_load", **load_result})

        if load_result["status"] != "success":
            raise Exception(f"Table load failed: {load_result.get('error')}")

        # Success
        results["status"] = "success"
        results["end_time"] = datetime.now().isoformat()
        print(f"✅ Successfully ingested RSS feed to {TABLE_NAME}")

    except Exception as e:
        results["status"] = "error"
        results["error"] = str(e)
        results["end_time"] = datetime.now().isoformat()
        print(f"❌ Ingestion failed: {str(e)}")
        sys.exit(1)

    finally:
        # Close session if exists
        if "session" in locals():
            session.close()

    return results


if __name__ == "__main__":
    # Run ingestion
    result = ingest_rss_feed()

    # Print summary
    print("\nIngestion Summary:")
    print(f"Status: {result['status']}")
    print(f"Start: {result['start_time']}")
    print(f"End: {result['end_time']}")

    if result["status"] == "error":
        print(f"Error: {result.get('error')}")
        sys.exit(1)
