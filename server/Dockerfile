FROM python:3.12-slim

# Install system-level dependencies (poppler-utils, ffmpeg, curl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create a non-root user with UID 1000 (Required by Hugging Face Spaces)
RUN useradd -m -u 1000 user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Install uv (extremely fast package installer) globally
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Copy dependency files
COPY pyproject.toml requirements.txt ./

# Install python dependencies globally in the container
RUN uv pip install --system --no-cache -r requirements.txt

# Copy application source code with correct ownership
COPY --chown=user:user app /app/app
COPY --chown=user:user main.py /app/main.py

# Create data directory and set ownership so user (UID 1000) can write to it
RUN mkdir -p /app/data && chown -R user:user /app/data

# Use non-root user (UID 1000)
USER user

EXPOSE 7860

# Health check using Python's standard library
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7860/health')" || exit 1

# Start FastAPI server binding to Hugging Face's default port 7860
CMD ["python", "-m", "uvicorn", "app.api.server:app", "--host", "0.0.0.0", "--port", "7860"]
