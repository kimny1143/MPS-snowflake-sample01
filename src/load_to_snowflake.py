import pandas as pd

from snowflake.snowpark import Session
from snowflake.snowpark.types import StringType, StructField, StructType, TimestampType


def create_table_if_not_exists(session: Session) -> None:
    ddl = """
    CREATE TABLE IF NOT EXISTS BLOG_POSTS (
        ID VARCHAR(36),
        TITLE VARCHAR(500),
        URL VARCHAR(500),
        PUBLISHED_AT TIMESTAMP_NTZ,
        BODY VARCHAR
    )
    """
    session.sql(ddl).collect()


def write_df(session: Session, df: pd.DataFrame) -> int:
    schema = StructType(
        [
            StructField("ID", StringType()),
            StructField("TITLE", StringType()),
            StructField("URL", StringType()),
            StructField("PUBLISHED_AT", TimestampType()),
            StructField("BODY", StringType()),
        ]
    )

    snowpark_df = session.create_dataframe(df, schema)
    snowpark_df.write.mode("append").save_as_table("BLOG_POSTS")

    return df.shape[0]
