#!/bin/bash

# Streamlit起動用ラッパースクリプト（エラー回避版）

echo "🚀 Streamlit を起動します..."

# Poetry PATHを確保
export PATH="$HOME/.local/bin:$PATH"

# ブラウザ自動起動を無効化してStreamlitを起動
# これによりFileNotFoundErrorを回避
export STREAMLIT_SERVER_HEADLESS=true
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

echo ""
echo "📌 以下のURLでアクセスできます:"
echo "   http://localhost:8501"
echo ""
echo "停止するには Ctrl+C を押してください"
echo ""

# Streamlit起動
poetry run streamlit run app/streamlit_app.py \
    --server.headless true \
    --browser.gatherUsageStats false
