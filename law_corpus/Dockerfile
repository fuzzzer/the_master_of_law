FROM python:3.11-slim

WORKDIR /app

# System dependencies for PDF/Georgian text processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

# Copy source
COPY . .

# Create data directories
RUN mkdir -p data/raw/html data/raw/pdf data/raw/metadata \
    data/parsed data/chunks data/embeddings data/index data/checkpoints

ENTRYPOINT ["python", "-m", "pipeline.main"]
CMD ["--help"]
