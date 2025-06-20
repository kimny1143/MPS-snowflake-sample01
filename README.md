# MPS-snowflake-sample01

note のRSSフィードをSnowflakeに取り込み、自動化されたデータパイプラインを構築するサンプルです。

## 🚀 クイックスタート（3コマンドで完了）

```bash
# 1. 環境構築（依存関係インストール + Snowflake初期化）
make bootstrap

# 2. RSS取込 + 自動化タスク起動
make ingest

# 3. WebUIで検索・分析
make ui
```

ブラウザで http://localhost:8501 を開いてください。

## アーキテクチャ

```
RSS Feed → RAW Layer (JSON) → STG Layer (正規化) → CORE Layer (ビジネス用)
              ↓                    ↓                    ↓
         内部ステージ           STREAM監視            5分ごと自動マージ
                                   ↓
                            OpenAI Embeddings → Semantic Search
```

## セットアップ手順（詳細版）

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

# OpenAI APIキー（セマンティック検索用）
OPENAI_API_KEY=your_openai_api_key
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

```
MPS-snowflake-sample01/
├─ README.md               # このファイル
├─ requirements.txt        # Python依存関係
├─ .env.example           # 環境変数の雛形
├─ Makefile               # 自動化コマンド
├─ snowflake/
│  ├─ setup.sql          # DB/テーブル/タスク定義
│  └─ embeddings.sql     # RAG用拡張
├─ src/
│  ├─ config.py          # Snowflake接続
│  ├─ fetch_rss.py       # RSS取得
│  ├─ loader.py          # データローダー
│  ├─ embeddings.py      # OpenAI連携
│  └─ models.py          # データモデル
├─ app/
│  └─ main.py            # Streamlit UI
└─ .github/
   └─ workflows/
      └─ pipeline.yml    # CI/CDパイプライン
```

## Makeコマンド一覧

| コマンド | 説明 |
|---------|------|
| `make bootstrap` | 完全セットアップ（依存関係 + DB初期化） |
| `make ingest` | RSS取込 + 自動化タスク起動 |
| `make status` | タスクとデータの状態確認 |
| `make merge` | 手動でSTG→COREマージ実行 |
| `make ui` | Streamlit WebUI起動 |
| `make clean` | 一時ファイルクリーンアップ |

## データベース構造

### レイヤー構成

1. **RAW Layer** (`MUED.RAW`)
   - `NOTE_RSS_RAW`: 生のRSSデータをJSON形式で保存

2. **STG Layer** (`MUED.STG`)
   - `NOTE_ARTICLES`: 正規化されたビュー
   - `NOTE_ARTICLES_STREAM`: 変更検知用ストリーム

3. **CORE Layer** (`MUED.CORE`)
   - `BLOG_POSTS`: ビジネス用の最終テーブル
   - `MERGE_BLOG_POSTS_TASK`: 5分ごとの自動マージタスク

## 10分で動くサンプルクエリ

```sql
-- RAWレイヤーの確認（JSON形式）
SELECT * FROM MUED.RAW.NOTE_RSS_RAW LIMIT 1;

-- STGレイヤーの確認（正規化済み）
SELECT TITLE, URL, PUBLISHED_AT 
FROM MUED.STG.NOTE_ARTICLES 
ORDER BY PUBLISHED_AT DESC LIMIT 10;

-- COREレイヤーの確認（重複排除済み）
SELECT COUNT(*) as TOTAL_POSTS FROM MUED.CORE.BLOG_POSTS;

-- 最新記事を取得
SELECT TITLE, URL, PUBLISHED_AT 
FROM MUED.CORE.BLOG_POSTS 
ORDER BY PUBLISHED_AT DESC LIMIT 5;

-- タスクの状態確認
SHOW TASKS IN DATABASE MUED;

-- ストリームの状態確認
SELECT SYSTEM$STREAM_HAS_DATA('MUED.STG.NOTE_ARTICLES_STREAM');
```

## 主な機能

### 1. 自動化されたデータパイプライン
- RSS フィードを定期的に取得
- STREAMとTASKで5分ごとに自動マージ
- 重複記事の自動排除

### 2. セマンティック検索（RAG）
- OpenAI Embeddingsで記事をベクトル化
- コサイン類似度による高速検索
- Streamlit UIで直感的に操作

### 3. CI/CDパイプライン
- GitHub Actionsで自動テスト
- Snowflakeへの自動デプロイ
- セキュリティスキャン付き

## トラブルシューティング

### タスクが動かない場合
```bash
make enable-task  # タスクを再開
```

### データが更新されない場合
```bash
make merge  # 手動マージ実行
make status  # 状態確認
```

### 埋め込みエラーの場合
- OPENAI_API_KEYが設定されているか確認
- OpenAI APIの利用制限を確認