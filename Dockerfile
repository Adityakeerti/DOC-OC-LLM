# Stage 1: Build React Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# Stage 2: Production Python Backend + Compiled UI
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies for PyMuPDF & Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application source
COPY api/ ./api/
COPY pipeline/ ./pipeline/
COPY dataset/ ./dataset/
COPY app.py .

# Copy compiled frontend from Stage 1 into frontend/dist
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

ENV PORT=8000
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Healthcheck for uptime monitors
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:${PORT}/health || exit 1

CMD ["python", "app.py"]
