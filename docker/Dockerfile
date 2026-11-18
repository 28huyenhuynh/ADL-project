# Image for the handbook chatbot (Flask web app + RAG pipeline).
# Ollama runs in its own container (see docker-compose.yml).
#
# Build from the project root:
#   docker build -f docker/Dockerfile -t handbook-rag ./source_code

FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HOST=0.0.0.0 \
    PORT=8000 \
    DATA_DIR=/app/data/handbook \
    VECTOR_STORE=/app/vector_store/handbook

WORKDIR /app

# Dependencies first, so code changes do not reinstall packages.
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY rag ./rag
COPY eval ./eval
COPY templates ./templates
COPY static ./static
COPY app.py cli.py tarot.py ./
COPY scripts ./scripts
# Documents are copied as a default, and can be replaced with a volume.
COPY data ./data

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/info')" || exit 1

# One worker (one shared vector store), several threads so streaming answers do not block each other.
CMD ["sh", "-c", "gunicorn -w 1 --threads 8 --timeout 600 -b ${HOST}:${PORT} app:app"]
