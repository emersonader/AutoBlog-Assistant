#!/bin/bash
# AutoBlog Assistant - Run Script

cd "$(dirname "$0")"

# Use Python 3.12 if available
if command -v /opt/homebrew/bin/python3.12 &> /dev/null; then
    PYTHON="/opt/homebrew/bin/python3.12"
    PIP="/opt/homebrew/bin/pip3.12"
elif command -v python3.12 &> /dev/null; then
    PYTHON="python3.12"
    PIP="pip3.12"
else
    PYTHON="python3"
    PIP="pip3"
fi

echo "Using $($PYTHON --version)"

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo ""
    echo "Please edit .env and add your GOOGLE_API_KEY"
    echo "Get one at: https://aistudio.google.com/apikey"
    exit 1
fi

# Install dependencies
$PIP install -q -r requirements.txt

# Create output folder
mkdir -p output

# Run the app
echo "Starting AutoBlog Assistant..."
echo "Open http://localhost:8501 in your browser"
echo ""
$PYTHON -m streamlit run app.py
