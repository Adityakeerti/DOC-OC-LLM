#!/bin/bash
set -e

PORT="${PORT:-7860}"
VLM_PORT=8080
MODEL_DIR="/app/models"
MODEL_PATH="$MODEL_DIR/gemma-4-E2B_q4_0-it.gguf"
MMPROJ_PATH="$MODEL_DIR/gemma-4-E2B-it-mmproj.gguf"

mkdir -p "$MODEL_DIR"

# 1. Download Model from Hugging Face if not already present
if [ ! -f "$MODEL_PATH" ] || [ ! -f "$MMPROJ_PATH" ]; then
    echo "📥 Downloading Gemma-4-E2B GGUF weights from Hugging Face..."
    python -c "
from huggingface_hub import hf_hub_download
import os

model_dir = '$MODEL_DIR'
print('Downloading base model...')
hf_hub_download(repo_id='google/gemma-4-E2B-it-GGUF', filename='gemma-4-E2B_q4_0-it.gguf', local_dir=model_dir)
print('Downloading vision projector...')
hf_hub_download(repo_id='google/gemma-4-E2B-it-GGUF', filename='gemma-4-E2B-it-mmproj.gguf', local_dir=model_dir)
print('✅ Models downloaded successfully!')
"
fi

# 2. Check for GPU availability
GPU_LAYERS=0
EXTRA_FLAGS=""
if command -v nvidia-smi &> /dev/null && nvidia-smi &> /dev/null; then
    echo "⚡ NVIDIA GPU detected! Enabling 100% GPU acceleration..."
    GPU_LAYERS=35
    EXTRA_FLAGS="--flash-attn on"
else
    echo "⚙️ Running on Free CPU Mode (16 GB RAM). Using 4 multi-threaded CPU workers..."
    GPU_LAYERS=0
    EXTRA_FLAGS=""
fi

# 3. Start llama-server in the background on port 8080
echo "🚀 Starting llama-server on port $VLM_PORT..."
llama-server \
    --model "$MODEL_PATH" \
    --mmproj "$MMPROJ_PATH" \
    --port $VLM_PORT \
    --host 127.0.0.1 \
    --n-gpu-layers $GPU_LAYERS \
    --ctx-size 8192 \
    --parallel 1 \
    --threads 4 \
    --reasoning off \
    --reasoning-budget 0 \
    $EXTRA_FLAGS &

LLAMA_PID=$!

# Wait for llama-server to become healthy
echo "⏳ Waiting for VLM inference server to initialize..."
until curl -s http://127.0.0.1:$VLM_PORT/health > /dev/null; do
    sleep 2
done
echo "✅ VLM Server ready on port $VLM_PORT!"

# 4. Start FastAPI server on public port (7860 on Hugging Face, or $PORT)
echo "🌐 Starting DOC-OC v2 Web Application on port $PORT..."
export VLM_API_URL="http://127.0.0.1:$VLM_PORT/v1/chat/completions"
exec python app.py
