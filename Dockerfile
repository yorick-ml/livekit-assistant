FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables from .env file
ENV PYTHONUNBUFFERED=1
ENV OPENAI_BASE_URL=http://192.168.88.56:11434/v1
ENV OPENAI_MODEL=qwen2.5:7b-instruct-q8_0
ENV STT_BASE_URL=http://192.168.88.56:8000/v1/

CMD ["python", "assistant.py"]
