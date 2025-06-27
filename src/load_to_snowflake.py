import pandas as pd
from snowflake.snowpark import Session
from snowflake.snowpark.types import StringType, StructField, StructType, TimestampType


def create_table_if_not_exists(session: Session) -> None:
    """テーブルが存在しない場合は作成

    Args:
        session: Snowflakeセッション
    """
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
    """データフレームをSnowflakeテーブルに書き込む

    Args:
        session: Snowflakeセッション
        df: 書き込むデータフレーム

    Returns:
        書き込んだ行数
    """
    # テーブルスキーマの定義
    schema = StructType(
        [
            StructField("ID", StringType()),
            StructField("TITLE", StringType()),
            StructField("URL", StringType()),
            StructField("PUBLISHED_AT", TimestampType()),
            StructField("BODY", StringType()),
        ]
    )

    # Snowpark DataFrameに変換してテーブルに追加
    snowpark_df = session.create_dataframe(df, schema)
    snowpark_df.write.mode("append").save_as_table("BLOG_POSTS")

    return df.shape[0]
