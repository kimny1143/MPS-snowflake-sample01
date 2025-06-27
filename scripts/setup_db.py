#!/usr/bin/env python
"""Setup Snowflake database objects"""

import sys

sys.path.insert(0, ".")

from src.config import get_session


def main():
    session = get_session()

    # First, ensure database exists
    try:
        print("Creating database MUED if not exists...")
        session.sql("CREATE DATABASE IF NOT EXISTS MUED").collect()
        session.sql("USE DATABASE MUED").collect()
        print("✓ Database MUED is ready")
    except Exception as e:
        print(f"Error setting up database: {e}")
        return

    with open("snowflake/setup.sql") as f:
        sql_content = f.read()

    # Skip the CREATE DATABASE and USE DATABASE statements since we already handled them
    statements = []
    for stmt in sql_content.split(";"):
        stmt = stmt.strip()
        if stmt and not stmt.startswith("--"):
            if not stmt.upper().startswith(
                "CREATE DATABASE"
            ) and not stmt.upper().startswith("USE DATABASE"):
                statements.append(stmt)

    for i, stmt in enumerate(statements, 1):
        try:
            print(f"Executing statement {i}/{len(statements)}...")
            session.sql(stmt).collect()
        except Exception as e:
            print(f"Warning: {e}")

    session.close()
    print("✓ Database setup complete")


if __name__ == "__main__":
    main()
