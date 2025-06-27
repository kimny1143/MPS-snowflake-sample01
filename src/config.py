import os

from dotenv import load_dotenv

from snowflake.snowpark import Session


def get_snowflake_session() -> Session:
    load_dotenv()

    connection_params = {
        "account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "user": os.getenv("SNOWFLAKE_USER"),
        "password": os.getenv("SNOWFLAKE_PASSWORD"),
        "role": os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
        "database": os.getenv("SNOWFLAKE_DATABASE", "MUED"),
        "schema": os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC"),
    }

    return Session.builder.configs(connection_params).create()
