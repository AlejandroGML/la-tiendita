# Stage 1: Build — install Python dependencies
FROM python:3.14-slim AS builder
WORKDIR /app
COPY backend/ ./
RUN pip install --no-cache-dir .

# Stage 2: Runtime — copy only what's needed
FROM python:3.14-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY backend/app/ ./app/
RUN mkdir -p uploads
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
