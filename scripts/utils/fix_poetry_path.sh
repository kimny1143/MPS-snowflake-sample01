#!/bin/bash
# Fix Poetry PATH issues

echo "=== Poetry PATH Fix ==="
echo ""
echo "Add the following line to your ~/.zshrc or ~/.bashrc file:"
echo ""
echo 'export PATH="$HOME/.local/bin:$PATH"'
echo ""
echo "Then reload your shell configuration:"
echo "source ~/.zshrc  # or source ~/.bashrc"
echo ""
echo "=== Alternative: Use Poetry Commands ==="
echo ""
echo "Instead of 'poetry shell', use:"
echo "1. poetry run <command>  # Run a single command"
echo "2. source \$(poetry env info --path)/bin/activate  # Manually activate"
echo ""
echo "=== For Streamlit ==="
echo ""
echo "To prevent browser opening errors, you can:"
echo "1. Run with --server.headless true:"
echo "   poetry run streamlit run app/streamlit_app.py --server.headless true"
echo ""
echo "2. Or set environment variable:"
echo "   export STREAMLIT_SERVER_HEADLESS=true"
echo "   poetry run streamlit run app/streamlit_app.py"
