import feedparser
import html2text
import pandas as pd
from datetime import datetime
from uuid import uuid4


def fetch(feed_url: str) -> pd.DataFrame:
    feed = feedparser.parse(feed_url)
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = True
    
    rows = []
    for entry in feed.entries:
        row = {
            "id": str(uuid4()),
            "title": entry.get("title", ""),
            "url": entry.get("link", ""),
            "published_at": datetime(*entry.published_parsed[:6]) if hasattr(entry, "published_parsed") else datetime.now(),
            "body": h.handle(entry.get("summary", "") or entry.get("content", [{}])[0].get("value", ""))
        }
        rows.append(row)
    
    return pd.DataFrame(rows, columns=["id", "title", "url", "published_at", "body"])