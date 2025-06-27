# Scripts Directory

このディレクトリには、プロジェクトで使用する各種スクリプトが整理されています。

## 📁 ディレクトリ構成

### setup/
Snowflake環境のセットアップ用スクリプト
- `setup_db.py` - データベースの初期設定
- `setup_tables.py` - テーブルの作成
- `setup_embeddings.py` - 埋め込み機能のセットアップ
- `create_chunks_proc.py` - チャンク処理用プロシージャの作成

### data/
データ処理・取得関連のスクリプト
- `ingest.py` - RSS フィードの取得と投入
- `fetch_full_article.py` - 記事の完全取得
- `enhance_articles.py` - 記事データの拡張
- `recreate_all_chunks.py` - チャンクの再作成
- `clean_session.py` - セッションのクリーンアップ

### debug/
デバッグ・動作確認用スクリプト
- `check_*.py` - 各種オブジェクトの確認
- `debug_search.py` - 検索機能のデバッグ
- `test_connection.py` - 接続テスト
- `status.py` - システムステータスの確認

### utils/
ユーティリティスクリプト
- `run_streamlit.sh` - Streamlit アプリの起動
- `fix_poetry_*.sh` - Poetry 環境の修正
- `activate_poetry.sh` - Poetry 環境の有効化

### fixes/
修正・パッチ用スクリプト
- `fix_cosine_function.py` - ベクトル距離関数の修正
- `simple_solution.py` - 簡易的な解決策の実装
