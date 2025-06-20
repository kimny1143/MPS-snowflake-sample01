# MPS-snowflake-sample01

note のRSSフィードをSnowflakeに取り込む最小構成のサンプルです。

## セットアップ手順

### 1. Anaconda環境の作成と有効化

```bash
conda create -n mps-snowflake python=3.12
conda activate mps-snowflake
```

### 2. 依存ライブラリのインストール

```bash
pip install -r requirements.txt
```

### 3. 環境変数の設定

`.env.example`をコピーして`.env`を作成し、Snowflakeの接続情報を設定します。

```bash
cp .env.example .env
```

`.env`ファイルを編集して実際の接続情報を入力：

```
SNOWFLAKE_ACCOUNT=your_account_identifier
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_ROLE=ACCOUNTADMIN
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=MUED
SNOWFLAKE_SCHEMA=PUBLIC
```

### 4. RSSフィードの取得とSnowflakeへの書き込み

```bash
python -m src.main https://note.com/mued_glasswerks/rss
```

### 5. データの確認

Snowflakeで以下のSQLを実行してデータを確認：

```sql
SELECT COUNT(*) FROM MUED.PUBLIC.BLOG_POSTS;

-- 最新10件を表示
SELECT * FROM MUED.PUBLIC.BLOG_POSTS 
ORDER BY PUBLISHED_AT DESC 
LIMIT 10;
```

## ファイル構成

- `requirements.txt` - 必要なPythonライブラリ
- `.env.example` - 環境変数の設定例
- `src/config.py` - Snowflake接続設定
- `src/fetch_rss.py` - RSSフィード取得処理
- `src/load_to_snowflake.py` - Snowflakeへのデータ書き込み
- `src/main.py` - メインの実行スクリプト

## テーブル構造

`MUED.PUBLIC.BLOG_POSTS`テーブル：

| カラム名 | データ型 | 説明 |
|---------|---------|------|
| ID | VARCHAR(36) | 記事の一意識別子（UUID） |
| TITLE | VARCHAR(500) | 記事タイトル |
| URL | VARCHAR(500) | 記事URL |
| PUBLISHED_AT | TIMESTAMP_NTZ | 公開日時 |
| BODY | VARCHAR | 記事本文（Markdown形式） |