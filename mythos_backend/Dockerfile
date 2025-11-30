# Base image for Python 3.11 for performance and modern syntax
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory inside the container
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY mythos_backend.py .

# The command to run the Uvicorn server (FastAPI) on port 8001
CMD ["uvicorn", "mythos_backend:app", "--host", "0.0.0.0", "--port", "8001"]