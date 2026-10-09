#!/bin/bash
# ──────────────────────────────────────────────────────────────────────────────
# start_server.sh — Launch the local VLM for DOC-OC v6
#
# Usage:
#   ./start_server.sh gemma        → Gemma-4-E2B            (100% GPU offload, 35 layers)
#   ./start_server.sh qwen         → Qwen2.5-VL-3B-Instruct (100% GPU offload, 36 layers)
#   ./start_server.sh uitars       → UI-TARS-7B-DPO         (20 GPU layers)
#   ./start_server.sh stop         → Kill running server
# ──────────────────────────────────────────────────────────────────────────────

LLAMA_SERVER="/home/aditya/llama-fork/build/bin/llama-server"
MODELS="/home/aditya/AI/models"
PORT=8080

# ── Stop command ──────────────────────────────────────────────────────────────

if [ "$1" = "stop" ]; then
    echo "Stopping llama-server..."
    pkill -f "llama-server.*--port $PORT" 2>/dev/null && echo "✅ Stopped" || echo "No server running"
    exit 0
fi

# ── Model selection ───────────────────────────────────────────────────────────

if [ "$1" = "gemma" ]; then
    MODEL="$MODELS/Gemma-4-E2B/gemma-4-E2B_q4_0-it.gguf"
    MMPROJ="$MODELS/Gemma-4-E2B/gemma-4-E2B-it-mmproj.gguf"
    MODEL_NAME="Gemma-4-E2B"
    GPU_LAYERS=35
elif [ "$1" = "qwen" ]; then
    MODEL="$MODELS/Qwen2.5-VL-3B-Instruct-GGUF/Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf"
    MMPROJ="$MODELS/Qwen2.5-VL-3B-Instruct-GGUF/mmproj-Qwen2.5-VL-3B-Instruct-f16.gguf"
    MODEL_NAME="Qwen2.5-VL-3B-Instruct"
    GPU_LAYERS=36
else
    MODEL="$MODELS/UI-TARS-7B-DPO/UI-TARS-7B-DPO-Q4_K_M.gguf"
    MMPROJ="$MODELS/UI-TARS-7B-DPO/mmproj-UI-TARS-7B-DPO-f16.gguf"
    MODEL_NAME="UI-TARS-7B-DPO"
    GPU_LAYERS=20
fi

# ── Verify files exist ────────────────────────────────────────────────────────

if [ ! -f "$MODEL" ]; then
    echo "❌ Model not found: $MODEL"
    exit 1
fi

if [ ! -f "$MMPROJ" ]; then
    echo "❌ Vision projector not found: $MMPROJ"
    exit 1
fi

# ── Ensure previous server on port is stopped ─────────────────────────────────

if pgrep -f "llama-server.*--port $PORT" > /dev/null; then
    echo "⚠️ Existing llama-server detected on port $PORT. Restarting..."
    pkill -f "llama-server.*--port $PORT" 2>/dev/null
    sleep 2
fi

# ── Launch ────────────────────────────────────────────────────────────────────

echo "╔════════════════════════════════════════════════════════╗"
echo "║  DOC-OC v6 — High-Performance VLM Inference Server    ║"
echo "╠════════════════════════════════════════════════════════╣"
echo "║  Model:      $MODEL_NAME"
echo "║  Port:       http://localhost:$PORT"
echo "║  GPU Offload: $GPU_LAYERS layers (100% on RTX 4050 VRAM)"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

$LLAMA_SERVER \
    --model "$MODEL" \
    --mmproj "$MMPROJ" \
    --port $PORT \
    --n-gpu-layers $GPU_LAYERS \
    --ctx-size 8192 \
    --parallel 1 \
    --threads 4 \
    --flash-attn on \
    --reasoning off \
    --reasoning-budget 0
