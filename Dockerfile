FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY requirements.txt .
COPY pyproject.toml .

RUN uv venv && \
    . .venv/bin/activate && \
    uv pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [".venv/bin/python", "main.py"]