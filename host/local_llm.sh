#!/bin/bash
# local/serve.sh: Run the quantized Ministral model on your local laptop.
# This is the "Compute Tax" — spinning up this server makes your fans scream.
#
# Prerequisites:
#   1. Run brev/siphon.sh first to get the .gguf file locally.
#   2. llama.cpp built at ~/dev/llama.cpp/build/

set -e

GGUF_PATH="./models/ministral-8b-Q4_K_M.gguf"
PORT=8000
HOST="127.0.0.1"

# Path to the llama.cpp build output (binary + shared libs live here together)
LLAMA_BUILD_BIN="$HOME/dev/llama.cpp/build/bin"
LLAMA_SERVER="$LLAMA_BUILD_BIN/llama-server"

# --- Sanity checks ---
if [ ! -f "$GGUF_PATH" ]; then
    echo "Model file not found at $GGUF_PATH"
    echo "Run: bash brev/siphon.sh"
    exit 1
fi

if [ ! -f "$LLAMA_SERVER" ]; then
    echo "llama-server not found at $LLAMA_SERVER"
    echo "Rebuild llama.cpp:"
    echo "cd ~/dev/llama.cpp && cmake -B build && cmake --build build -j\$(nproc)"
    exit 1
fi

echo "Starting local Ministral inference server..."
echo "Model : $GGUF_PATH"
echo "Listen: http://$HOST:$PORT"
echo "success."


# Prepend build/bin to LD_LIBRARY_PATH so libmtmd.so.0 and friends are found
export LD_LIBRARY_PATH="$LLAMA_BUILD_BIN:${LD_LIBRARY_PATH:-}"

# --n-gpu-layers 35: offloads layers to GPU if available (CUDA on Linux)
# --ctx-size 4096: enough context for 15 × 2s window entries
# --parallel 1: single user, no need for multi-slot batching
"$LLAMA_SERVER" \
    --model "$GGUF_PATH" \
    --host "$HOST" \
    --port "$PORT" \
    --n-gpu-layers 35 \
    --ctx-size 4096 \
    --parallel 1 \
    --log-disable
