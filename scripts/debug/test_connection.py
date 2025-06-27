#!/usr/bin/env python
"""Test Snowflake connection"""

import sys

sys.path.insert(0, ".")

from src.config import get_session


def main():
    print("Testing Snowflake connection...")
    print("Reading environment variables...")

    import os

    from dotenv import load_dotenv

    load_dotenv()

    print(f"Account: {os.getenv('SNOWFLAKE_ACCOUNT')}")
    print(f"User: {os.getenv('SNOWFLAKE_USER')}")
    print(f"Database: {os.getenv('SNOWFLAKE_DATABASE')}")
    print(f"Schema: {os.getenv('SNOWFLAKE_SCHEMA')}")
    print(f"Role: {os.getenv('SNOWFLAKE_ROLE')}")
    print(f"Warehouse: {os.getenv('SNOWFLAKE_WAREHOUSE')}")

    try:
        session = get_session()
        result = session.sql(
            "SELECT CURRENT_USER(), CURRENT_DATABASE(), CURRENT_SCHEMA()"
        ).collect()
        print("\n✅ Connection successful!")
        print(f"User: {result[0][0]}")
        print(f"Database: {result[0][1]}")
        print(f"Schema: {result[0][2]}")
        session.close()
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        print("\nPlease check your .env file and ensure:")
        print("1. Password is correct")
        print("2. Account identifier format is correct")
        print("3. User has necessary permissions")


if __name__ == "__main__":
    main()
