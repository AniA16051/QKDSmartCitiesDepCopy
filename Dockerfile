FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_RETRIES=10 \
    PIP_DEFAULT_TIMEOUT=120

COPY requirements.txt ./
RUN pip install --no-cache-dir --retries 10 --timeout 120 -r requirements.txt

COPY . ./

# Railway provides PORT at runtime; 8501 keeps the image convenient locally.
EXPOSE 8501

CMD ["sh", "-c", "streamlit run dashboard/app_enhanced.py --server.address=0.0.0.0 --server.port=${PORT:-8501} --logger.level=warning"]
