#!/bin/bash
# Render deployment script for Streamlit with file watching disabled

# Set environment variables to disable file watching
export STREAMLIT_SERVER_FILE_WATCHER_TYPE="none"
export STREAMLIT_LOGGER_LEVEL="warning"

# Run Streamlit with file watching disabled
streamlit run app.py --server.headless=true --server.port=8501 --logger.level=warning