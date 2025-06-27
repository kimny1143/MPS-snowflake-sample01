import sys

from .config import get_session
from .loader import enable_task, execute_merge, get_task_status, load_rss_to_raw


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m src.main <RSS_URL>")
        sys.exit(1)

    feed_url = sys.argv[1]

    print("Establishing Snowflake session...")
    session = get_session()

    try:
        print(f"Loading RSS feed from {feed_url} to RAW layer...")
        load_result = load_rss_to_raw(session, feed_url)
        print(f"Load result: {load_result}")

        if load_result["status"] == "success":
            print("Executing merge to CORE layer...")
            merge_result = execute_merge(session)
            print(f"Merge result: {merge_result}")

            print("Enabling automatic merge task...")
            task_result = enable_task(session)
            print(f"Task result: {task_result}")

            print("\nCurrent task status:")
            task_df = get_task_status(session)
            print(task_df[["name", "state", "schedule"]].to_string())

            print("\n✓ RSS ingestion pipeline successfully set up!")
        else:
            print(f"❌ Error loading RSS: {load_result.get('error')}")
            sys.exit(1)

    finally:
        session.close()


if __name__ == "__main__":
    main()
