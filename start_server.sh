#!/bin/bash
# ──────────────────────────────────────────────────────────────────────────────
# start_server.sh — Launch the local VLM for DOC-OC v6
#
# Usage:
#   ./start_server.sh              → UI-TARS-7B-DPO (best for documents)
#   ./start_server.sh gemma        → Gemma-4-E2B    (faster, less VRAM)
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
    GPU_LAYERS=33
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

# ── Launch ────────────────────────────────────────────────────────────────────

echo "╔══════════════════════════════════════════╗"
echo "║  DOC-OC v6 — VLM Server                 ║"
echo "╠══════════════════════════════════════════╣"
echo "║  Model:  $MODEL_NAME"
echo "║  Port:   http://localhost:$PORT"
echo "║  GPU:    $GPU_LAYERS layers offloaded"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "Press Ctrl+C to stop"
echo ""

$LLAMA_SERVER \
    --model "$MODEL" \
    --mmproj "$MMPROJ" \
    --port $PORT \
    --n-gpu-layers $GPU_LAYERS \
    --ctx-size 8192 \
    --threads 4 \
    --flash-attn on
