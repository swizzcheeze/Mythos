# Mythos Backend — NVIDIA CUDA (default)
# For NVIDIA GPU users. Supports GPU-accelerated embeddings with CPU fallback.
#
# Port is configurable via MYTHOS_PORT env var (default: 8013).
# Build context must be the repo root (.), not this directory.
FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

# Install Python 3.11
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Create symlinks for python and pip (remove existing first)
RUN rm -f /usr/bin/python /usr/bin/pip && \
    ln -s /usr/bin/python3.11 /usr/bin/python && \
    ln -s /usr/bin/pip3 /usr/bin/pip

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV MYTHOS_PORT=8013
# Fix for torch multiprocessing issues in Docker
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1
ENV TORCH_NUM_THREADS=1

# Set the working directory inside the container
WORKDIR /app

# Copy and install dependencies
COPY mythos_backend/requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy the application package
COPY mythos_backend/ ./mythos_backend/

# Run on the port configured via MYTHOS_PORT
CMD ["sh", "-c", "uvicorn mythos_backend.main:app --host 0.0.0.0 --port ${MYTHOS_PORT:-8013} --workers 1 --no-access-log"]
