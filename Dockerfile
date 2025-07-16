FROM python:3.11-slim

# Устанавливаем tzdata для поддержки часовых поясов
RUN apt-get update && apt-get install -y tzdata && rm -rf /var/lib/apt/lists/*

# Часовой пояс будет задаваться через переменную TZ из .env
ENV TZ=Europe/Moscow
RUN ln -sf /usr/share/zoneinfo/$TZ /etc/localtime && echo "$TZ" > /etc/timezone

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY requirements.txt .
COPY pyproject.toml .

RUN uv venv && \
    . .venv/bin/activate && \
    uv pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [".venv/bin/python", "main.py"]