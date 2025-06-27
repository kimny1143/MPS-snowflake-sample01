# GitHub Actions Workflows

このディレクトリには、プロジェクトの自動化ワークフローが含まれています。

## ワークフロー一覧

### 1. Daily RSS Ingestion (`daily_ingest.yml`)
- **目的**: RSS フィードを毎日自動的に取得し、Snowflake に投入
- **実行タイミング**:
  - 毎日 UTC 3:00 (JST 12:00)
  - 手動実行も可能
- **必要なシークレット**:
  - `SNOWFLAKE_ACCOUNT`
  - `SNOWFLAKE_USER`
  - `SNOWFLAKE_PASSWORD`
  - `SNOWFLAKE_ROLE`
  - `SNOWFLAKE_WAREHOUSE`
  - `SNOWFLAKE_DATABASE`
  - `SNOWFLAKE_SCHEMA`
  - `RSS_FEED_URL`

### 2. PR Checks (`pr_checks.yml`)
- **目的**: プルリクエスト時のコード品質チェック
- **実行タイミング**:
  - PR 作成/更新時
  - main ブランチへのプッシュ時
- **チェック内容**:
  - **Lint**: Ruff と Black によるコードスタイルチェック
  - **Test**: PyTest によるユニットテスト実行
  - **Security**: Trivy による脆弱性スキャン

## セットアップ方法

### GitHub シークレットの設定

1. リポジトリの Settings → Secrets and variables → Actions に移動
2. 以下のシークレットを追加:

```bash
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_ROLE=ACCOUNTADMIN
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=MUED
SNOWFLAKE_SCHEMA=PUBLIC
RSS_FEED_URL=https://note.com/api/v2/creators/mued/contents?kind=note&page=1
```

## トラブルシューティング

### Daily Ingestion が失敗する場合
- Snowflake の認証情報を確認
- RSS_FEED_URL が正しいか確認
- Snowflake のウェアハウスが起動しているか確認

### PR Checks が失敗する場合
- ローカルで `make lint` と `make test` を実行して修正
- Poetry の依存関係が最新か確認 (`poetry lock --no-update`)

## 手動実行

Actions タブから各ワークフローを手動で実行できます:
1. Actions タブを開く
2. 実行したいワークフローを選択
3. "Run workflow" ボタンをクリック
