#!/bin/bash

# Usage: ./run.sh <API_KEY> [DOCX_FILE]
# Usage: ./run.sh [API_KEY] [DOCX_FILE]
# Example: ./run.sh
# Example: ./run.sh AIzaSy... test_sample.docx

# If first arg looks like an API key (starts with AI), use it.
# Otherwise, if it ends in .docx, it's the file.
# If nothing provided, we rely on .env

# Load .env if it exists (Explicit loading for bash)
if [ -f .env ]; then
  export $(cat .env | xargs)
fi

DOCX_FILE="test_sample.docx"
API_KEY=""

if [[ "$1" == *.docx ]]; then
  DOCX_FILE="$1"
elif [ -n "$1" ]; then
  API_KEY="$1"
  if [[ "$2" == *.docx ]]; then
    DOCX_FILE="$2"
  fi
fi

if [ -n "$API_KEY" ]; then
  export GOOGLE_API_KEY="$API_KEY"
fi

if [ ! -f "$DOCX_FILE" ]; then
    echo "File $DOCX_FILE not found. Generating default test file..."
    ./venv/bin/python generate_test_docx.py
fi

echo "Running prototype with file: $DOCX_FILE"
./venv/bin/python main.py "$DOCX_FILE"
