FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir poetry==2.1.3 && \
    poetry config virtualenvs.create false

# Copy dependency files first for layer caching
COPY backend/pyproject.toml backend/poetry.lock ./
RUN poetry install --only main --no-interaction

# Copy backend source and data (built from repo root)
COPY backend/ .
COPY data/ /data/

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
