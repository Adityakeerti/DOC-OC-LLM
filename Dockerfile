# Stage 1: Build React Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Build llama-server from source (universal CPU + CUDA compatible)
FROM ubuntu:22.04 AS llama-builder
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    git build-essential cmake ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 https://github.com/ggml-org/llama.cpp.git /llama.cpp && \
    cmake -B /llama.cpp/build -S /llama.cpp -DGGML_BUILD_EXAMPLES=OFF -DGGML_BUILD_SERVER=ON && \
    cmake --build /llama.cpp/build --target llama-server -j$(nproc)

# Stage 3: Final Production Container (Hugging Face Spaces & Cloud Compatible)
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy llama-server binary from Stage 2
COPY --from=llama-builder /llama.cpp/build/bin/llama-server /usr/local/bin/llama-server

# Set up user for Hugging Face Spaces compliance (uid 1000)
RUN useradd -m -u 1000 user
ENV HOME=/home/user
ENV PATH="/home/user/.local/bin:$PATH"

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source files
COPY api/ ./api/
COPY pipeline/ ./pipeline/
COPY dataset/ ./dataset/
COPY app.py entrypoint.sh ./
RUN chmod +x entrypoint.sh

# Copy compiled frontend from Stage 1 into frontend/dist
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Create models cache directory owned by user
RUN mkdir -p /app/models && chown -R user:user /app

USER user

ENV PORT=7860
ENV PYTHONUNBUFFERED=1
EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:${PORT}/health || exit 1

CMD ["./entrypoint.sh"]
