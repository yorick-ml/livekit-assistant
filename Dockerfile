FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and local package first to leverage Docker cache
COPY requirements.txt .
COPY dist/livekit_plugins_silero-0.7.4-py3-none-any.whl .
RUN pip install --no-cache-dir -r requirements.txt livekit_plugins_silero-0.7.4-py3-none-any.whl

# Copy application code
COPY . .

# Set Python to unbuffered mode
ENV PYTHONUNBUFFERED=1

CMD ["python", "assistant.py"]
