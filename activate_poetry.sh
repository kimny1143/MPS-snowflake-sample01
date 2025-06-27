#!/bin/bash
# Script to properly activate Poetry environment

# Add Poetry to PATH
export PATH="$HOME/.local/bin:$PATH"

# Get the virtual environment path
VENV_PATH=$(poetry env info --path)

if [ -z "$VENV_PATH" ]; then
    echo "Error: Could not find Poetry virtual environment"
    exit 1
fi

echo "Activating Poetry environment at: $VENV_PATH"

# Source the activation script
source "$VENV_PATH/bin/activate"

# Verify activation
echo "Python: $(which python)"
echo "PATH: $PATH"

# Test commands
echo -e "\nTesting commands:"
echo "clear command: $(which clear)"
echo "open command: $(which open)"

echo -e "\nEnvironment activated! You can now use 'clear' and 'open' commands."
echo "To run Streamlit: streamlit run app/streamlit_app.py"
