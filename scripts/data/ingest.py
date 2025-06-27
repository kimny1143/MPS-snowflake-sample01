#!/usr/bin/env python
"""Ingest RSS feed into Snowflake"""

import sys

sys.path.insert(0, ".")

from src.loader import enable_task, execute_merge, get_session, load_rss_to_raw


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/ingest.py <RSS_URL>")
        sys.exit(1)

    feed_url = sys.argv[1]
    session = get_session()

    # Load RSS
    result = load_rss_to_raw(session, feed_url)
    print(f"Load result: {result}")

    # Execute merge
    merge_result = execute_merge(session)
    print(f"Merge result: {merge_result}")

    # Enable task
    task_result = enable_task(session)
    print(f"Task result: {task_result}")

    session.close()
    print("✓ RSS loaded and task scheduler started")


if __name__ == "__main__":
    main()
