#!/bin/bash
# serve.sh: Launch vLLM with Ministral

MODEL="mistralai/Ministral-8B-Instruct-2410"

# Launch with 4-bit quantization to save memory and increase throughput
python -m vllm.entrypoints.openai.api_server \
    --model $MODEL \
    --quantization awq \
    --port 8000 \
    --host 0.0.0.0
