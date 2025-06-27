#!/usr/bin/env python
"""Show system status"""

import sys

sys.path.insert(0, ".")

from src.config import get_session
from src.loader import get_task_status


def main():
    session = get_session()

    print("=== Task Status ===")
    try:
        df = get_task_status(session)
        if not df.empty:
            # 実際の列名を確認して表示
            cols = df.columns.tolist()
            # Snowflakeは大文字の列名を返すことが多い
            display_cols = []
            for col in ["NAME", "STATE", "SCHEDULE", "name", "state", "schedule"]:
                if col in cols:
                    display_cols.append(col)
            if display_cols:
                print(df[display_cols].to_string())
            else:
                print("Tasks found but columns not recognized")
                print(f"Available columns: {cols[:5]}")  # 最初の5列を表示
        else:
            print("No tasks found")
    except Exception as e:
        print(f"Error getting task status: {e}")

    print("\n=== Data Status ===")
    tables = [
        "RAW.NOTE_RSS_RAW",
        "CORE.BLOG_POSTS",
        "STG.ARTICLE_CHUNKS",
        "STG.ARTICLE_EMBEDDINGS",
    ]
    for table in tables:
        try:
            count = session.sql(f"SELECT COUNT(*) as cnt FROM {table}").collect()[0][
                "CNT"
            ]
            print(f"{table}: {count} rows")
        except:
            print(f"{table}: N/A")

    session.close()


if __name__ == "__main__":
    main()
