#!/bin/bash

# Poetry環境の問題を修正するスクリプト

echo "🔧 Poetry環境の修正を開始します..."

# 1. Poetry PATHの永続的な設定
echo ""
echo "1️⃣ ~/.zshrcにPoetry PATHを追加します"
if ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' ~/.zshrc; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
    echo "✅ PATHを追加しました"
else
    echo "✅ すでにPATHが設定されています"
fi

# 2. Poetry環境のアクティベート方法を表示
echo ""
echo "2️⃣ Poetry環境のアクティベート方法:"
echo ""
echo "方法1: Poetry envを使う"
echo "  poetry env use python3.12"
echo "  source $(poetry env info --path)/bin/activate"
echo ""
echo "方法2: 直接activateする"
VENV_PATH=$(poetry env info --path 2>/dev/null)
if [ -n "$VENV_PATH" ]; then
    echo "  source $VENV_PATH/bin/activate"
else
    echo "  # まずpoetry installを実行してください"
fi

# 3. clearコマンドの確認
echo ""
echo "3️⃣ clearコマンドの場所を確認:"
which clear || echo "❌ clearが見つかりません"
echo "システムのclear: $(command -v /usr/bin/clear || echo "見つかりません")"

# 4. エイリアスの設定を提案
echo ""
echo "4️⃣ 便利なエイリアスを~/.zshrcに追加できます:"
echo ""
echo "# Poetry shortcuts"
echo "alias pa='source \$(poetry env info --path)/bin/activate'"
echo "alias pr='poetry run'"
echo "alias prs='poetry run streamlit run app/streamlit_app.py --server.headless true'"
echo "alias pra='poetry run uvicorn api.main:app --reload'"

echo ""
echo "✅ 今すぐ設定を反映するには以下を実行:"
echo "  source ~/.zshrc"
