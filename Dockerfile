FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libpq-dev \
    libmagic1 \
    libmagic-dev \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-heb \
    tesseract-ocr-ara \
    libreoffice \
    pandoc \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==1.7.1

# Configure poetry - disable virtualenv creation
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

# Copy poetry files
COPY pyproject.toml poetry.lock* ./

# Install dependencies directly (no virtualenv needed in container)
RUN poetry install --no-dev --no-root && rm -rf $POETRY_CACHE_DIR

# Production stage
FROM base as production

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY alembic.ini ./
COPY migrations/ ./migrations/

# Create directories
RUN mkdir -p /app/uploads /app/logs /app/models

# Expose port
EXPOSE 8000

# Start uvicorn on port 8000 (Railway target port is configured to 8000)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Development stage
FROM base as development

# Install dev dependencies
RUN poetry install && rm -rf $POETRY_CACHE_DIR

# Copy application code
COPY . .

# Command for development
CMD ["poetry", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
