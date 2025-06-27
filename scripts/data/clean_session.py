#!/usr/bin/env python
"""Clean Snowflake session and check functions"""

import sys

sys.path.insert(0, ".")

from src.config import get_session


def main():
    session = get_session()

    try:
        print("Cleaning Snowflake session...")

        session.sql("USE DATABASE MUED").collect()

        # Drop all cosine similarity functions
        print("\n1. Dropping old functions...")
        try:
            functions = session.sql(
                "SHOW FUNCTIONS LIKE '%COSINE%' IN SCHEMA STG"
            ).collect()
            for func in functions:
                func_name = func[1]
                print(f"  Dropping {func_name}")
                session.sql(f"DROP FUNCTION IF EXISTS STG.{func_name}").collect()
        except Exception as e:
            print(f"  Error: {e}")

        # Check for any functions with CORRELATION
        print("\n2. Checking for CORRELATION functions...")
        try:
            functions = session.sql("SHOW FUNCTIONS IN SCHEMA STG").collect()
            for func in functions:
                print(f"  Found: {func[1]}")
        except Exception as e:
            print(f"  Error: {e}")

        # Clear any hanging queries
        print("\n3. Clearing session...")
        session.sql("SELECT 1").collect()  # Simple query to clear state

        print("\n✓ Session cleaned")

        session.close()

    except Exception as e:
        print(f"Error: {e}")
        session.close()


if __name__ == "__main__":
    main()
