#!/bin/bash
# serve.sh: Launch vLLM with Ministral

MODEL="mistralai/Ministral-8B-Instruct-2410"

# Launch in native bfloat16 (no quantization)
# The L4 has 24GB VRAM, enough for 8B model (~16GB)
# max-model-len caps context to 16K to fit KV cache in remaining VRAM (~3.6GB)
python -m vllm.entrypoints.openai.api_server \
    --model $MODEL \
    --max-model-len 16384 \
    --port 8000 \
    --host 0.0.0.0
