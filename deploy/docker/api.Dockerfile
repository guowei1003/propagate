FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev

COPY apps/api /app/apps/api
COPY agents /app/agents
COPY evals /app/evals

ENV PYTHONPATH=/app/apps/api
ENV PATH=/app/.venv/bin:$PATH

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
