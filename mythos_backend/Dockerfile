# Base image with CUDA support for GPU embeddings (with CPU fallback)
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

# The command to run the Uvicorn server (FastAPI) on port 8001
CMD ["uvicorn", "mythos_backend.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1", "--no-access-log"]
