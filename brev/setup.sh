#!/bin/bash
# setup.sh: Setup a Brev instance for Ministral optimization

# Install vLLM for high-throughput serving
pip install vllm mistral-common weave

# Optional: Install Flash Attention 2 for better performance
pip install flash-attn --no-build-isolation

# Login to W&B if needed
# brew login ... (handled via env vars usually)

echo "Brev instance setup complete for Ministral."
