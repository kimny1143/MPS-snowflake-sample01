import sys
from config import get_session
from fetch_rss import fetch
from load_to_snowflake import create_table_if_not_exists, write_df


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m src.main <RSS_URL>")
        sys.exit(1)
    
    feed_url = sys.argv[1]
    
    print("Establishing Snowflake session...")
    session = get_session()
    
    print("Ensuring BLOG_POSTS table exists...")
    create_table_if_not_exists(session)
    
    print(f"Fetching RSS feed from {feed_url}...")
    df = fetch(feed_url)
    
    print(f"Writing {len(df)} posts to Snowflake...")
    rows_written = write_df(session, df)
    
    print(f"✓ Successfully wrote {rows_written} rows to BLOG_POSTS table")
    
    session.close()


if __name__ == "__main__":
    main()