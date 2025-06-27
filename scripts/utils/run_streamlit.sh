#!/bin/bash
# Wrapper script to run Streamlit with Poetry

# Add Poetry to PATH
export PATH="$HOME/.local/bin:$PATH"

# Ensure we're in the correct directory
cd "$(dirname "$0")"

# Run Streamlit with Poetry
echo "Starting Streamlit app..."
poetry run streamlit run app/streamlit_app.py \
    --server.address localhost \
    --server.port 8501 \
    --browser.gatherUsageStats false

# If the above fails with browser error, try headless mode:
# poetry run streamlit run app/streamlit_app.py --server.headless true
