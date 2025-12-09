#!/bin/bash
# Load .env variables just in case, though Streamlit/Python loads them too if using dotenv
if [ -f .env ]; then
  export $(cat .env | xargs)
fi

echo "Starting Web Application..."
echo "Access at http://localhost:8501"
./venv/bin/streamlit run app.py
