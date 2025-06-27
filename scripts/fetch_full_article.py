#!/usr/bin/env python
"""Fetch full article content from note.com"""

import sys

sys.path.insert(0, ".")
import time

from src.config import get_session


def fetch_article_content(url: str) -> str:
    """Fetch full article content from note.com URL"""
    # WebFetchツールを使った例（Claude Code内で動作）
    # 実際の実装では、requests + BeautifulSoupまたはSeleniumを使用

    # Note: これは例示的なコードです
    # 実際にはnote.comの利用規約を確認し、適切な方法で実装する必要があります
    print(f"Fetching content from: {url}")

    # ここでWebスクレイピングまたはAPIを使用
    # 簡易的な実装例：
    try:
        import requests
        from bs4 import BeautifulSoup

        headers = {"User-Agent": "Mozilla/5.0 (compatible; RSS-to-Snowflake/1.0)"}

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")

            # noteの記事本文を取得（セレクタは変更される可能性あり）
            # これは仮のセレクタです
            content_div = soup.find("div", class_="note-common-styles__textnote-body")
            if content_div:
                return content_div.get_text(strip=True)

            # 別のセレクタパターンを試す
            article_body = soup.find(
                "div", {"class": ["p-article__content", "note-body"]}
            )
            if article_body:
                return article_body.get_text(strip=True)

        return ""
    except Exception as e:
        print(f"Error fetching article: {e}")
        return ""


def update_articles_with_full_content(session, limit: int = 5):
    """Update articles with full content"""
    try:
        # 短い記事を取得
        short_articles = session.sql(
            f"""
            SELECT ID, URL, TITLE, BODY, LENGTH(BODY) as body_length
            FROM CORE.BLOG_POSTS
            WHERE LENGTH(BODY) < 500
            ORDER BY PUBLISHED_AT DESC
            LIMIT {limit}
        """
        ).collect()

        updated_count = 0
        for article in short_articles:
            print(f"\nProcessing: {article['TITLE']}")
            print(f"Current length: {article['BODY_LENGTH']} chars")

            # フルコンテンツを取得
            full_content = fetch_article_content(article["URL"])

            if full_content and len(full_content) > len(article["BODY"]):
                # データベースを更新
                session.sql(
                    f"""
                    UPDATE CORE.BLOG_POSTS
                    SET BODY = '{full_content.replace("'", "''")}'
                    WHERE ID = '{article['ID']}'
                """
                ).collect()

                print(f"✓ Updated with {len(full_content)} chars")
                updated_count += 1
            else:
                print("✗ No additional content found")

            # レート制限対策
            time.sleep(2)

        return updated_count

    except Exception as e:
        print(f"Error: {e}")
        return 0


def main():
    session = get_session()

    print("=== Full Article Content Fetcher ===\n")
    print("注意: このスクリプトはデモ目的です。")
    print("実際の使用前にnote.comの利用規約を確認してください。\n")

    # 別のアプローチ：RSS拡張サービスを使用
    print("代替案：")
    print("1. Full-Text RSS サービス (https://fivefilters.org/content-only/)")
    print("2. Mercury Parser API")
    print("3. Diffbot API")
    print("4. 手動でMarkdownファイルとして記事をエクスポート\n")

    # 現在のデータで進める
    print("現在の要約データでRAGシステムを構築することもできます。")
    print("要約でも以下が可能です：")
    print("- 記事の概要検索")
    print("- タイトルベースの推薦")
    print("- トピック分類")

    session.close()


if __name__ == "__main__":
    main()
