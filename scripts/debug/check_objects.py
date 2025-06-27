#!/usr/bin/env python
"""Check Snowflake objects"""

import sys

sys.path.insert(0, ".")

from src.config import get_session


def main():
    session = get_session()
    try:
        print("Checking database objects...")

        # Check schemas
        schemas = session.sql("SHOW SCHEMAS IN DATABASE MUED").collect()
        print(f"\nSchemas created: {len(schemas)}")
        for s in schemas:
            print(f"  - {s[1]}")

        # Check tables
        tables = session.sql("SHOW TABLES IN DATABASE MUED").collect()
        print(f"\nTables created: {len(tables)}")
        for t in tables:
            print(f"  - {t[1]}.{t[2]}")

        # Check views
        views = session.sql("SHOW VIEWS IN DATABASE MUED").collect()
        print(f"\nViews created: {len(views)}")
        for v in views:
            print(f"  - {v[1]}.{v[2]}")

        # Check procedures
        try:
            procs = session.sql("SHOW PROCEDURES IN DATABASE MUED").collect()
            print(f"\nProcedures created: {len(procs)}")
            for p in procs:
                print(f"  - {p[1]}.{p[2]}")
        except:
            print("\nProcedures: Unable to check")

        # Check tasks
        try:
            tasks = session.sql("SHOW TASKS IN DATABASE MUED").collect()
            print(f"\nTasks created: {len(tasks)}")
            for t in tasks:
                print(f"  - {t[1]}.{t[2]}")
        except:
            print("\nTasks: Unable to check")

        session.close()
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
