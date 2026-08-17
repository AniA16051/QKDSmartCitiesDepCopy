#!/usr/bin/env bash
# Render deployment script for Streamlit with dynamic port binding and file watching disabled

set -e

export STREAMLIT_SERVER_FILE_WATCHER_TYPE="none"
export STREAMLIT_LOGGER_LEVEL="warning"
export STREAMLIT_SERVER_HEADLESS="true"
export STREAMLIT_SERVER_ADDRESS="0.0.0.0"

PORT="${PORT:-8501}"

# Run Streamlit with dynamic port binding
streamlit run app.py --server.headless=true --server.address=0.0.0.0 --server.port="${PORT}" --server.fileWatcherType=none --logger.level=warning