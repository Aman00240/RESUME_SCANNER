FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

COPY requirements.txt .

RUN uv pip install --system --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn","backend.main:app","--host","0.0.0.0","--port","8000"]



