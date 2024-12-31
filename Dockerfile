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
ENV SILERO_MODEL=silero_tts
ENV SILERO_MODEL_ID=v4_ru
ENV SILERO_LANGUAGE=ru
ENV SILERO_SAMPLE_RATE=24000
ENV SILERO_SPEAKER=aidar
ENV SILERO_CPU_CORES=8
ENV ASSISTANT_PROMPT=Тебя зовут Кош. Ты - эксцентричный и токсичный бот, легко выходящий из себя. Отвечай на русском языке. Никогда не переходи на КИТАЙСКИЙ!

CMD ["python", "assistant.py"]
