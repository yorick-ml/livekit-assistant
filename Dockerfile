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

# Copy .env_sample as .env
COPY .env_sample .env

# Set Python to unbuffered mode
ENV PYTHONUNBUFFERED=1

CMD ["python", "assistant.py"]
