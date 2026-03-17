#!/bin/bash
# start.sh — runs both FastAPI and Streamlit together

echo "Starting InterviewCopilot AI..."

# Start FastAPI in background
uvicorn api.main:app --host 0.0.0.0 --port 8000 &

# Wait for FastAPI to be ready
sleep 3

# Start Streamlit in foreground
streamlit run app/streamlit_app.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --server.enableCORS false \
    --server.enableXsrfProtection false