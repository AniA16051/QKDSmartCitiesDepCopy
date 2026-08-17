#!/usr/bin/env python3
"""
Streamlit Cloud Entry Point
Re-exports the unified app.py logic for seamless deployment on share.streamlit.io
"""

from app import main

if __name__ == "__main__":
    main()