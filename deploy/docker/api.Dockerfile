FROM python:3.11-slim

WORKDIR /app

# context is ../backend, so requirements.txt is at the compose root level,
# COPY from compose root into /app
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# backend/ sources live at /app/backend inside the container
COPY ./app ./app
COPY ./services ./services
COPY ./routers ./routers
COPY ./models.py .
COPY ./schemas.py .
COPY ./config.py .
COPY ./db.py .

EXPOSE 8000

# Module path: backend.app.main → /app/backend/app/main.py
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
