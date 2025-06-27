from datetime import datetime
from uuid import uuid4

import feedparser
import html2text
import pandas as pd


def fetch(feed_url: str) -> pd.DataFrame:
    """RSS フィードを取得してDataFrameに変換

    Args:
        feed_url: RSS フィードのURL

    Returns:
        記事データのDataFrame (id, title, url, published_at, body)
    """
    # フィードをパース
    feed = feedparser.parse(feed_url)

    # HTML→テキスト変換器の設定
    h = html2text.HTML2Text()
    h.ignore_links = False  # リンクは保持
    h.ignore_images = True  # 画像は無視

    # 各エントリーを処理
    rows = []
    for entry in feed.entries:
        row = {
            "id": str(uuid4()),
            "title": entry.get("title", ""),
            "url": entry.get("link", ""),
            "published_at": datetime(*entry.published_parsed[:6]).isoformat()
            if hasattr(entry, "published_parsed")
            else datetime.now().isoformat(),
            "body": h.handle(
                entry.get("summary", "")  # 要約を優先
                or entry.get("content", [{}])[0].get("value", "")  # なければ本文
            ),
        }
        rows.append(row)

    return pd.DataFrame(rows, columns=["id", "title", "url", "published_at", "body"])
