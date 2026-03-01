#!/bin/bash
# setup.sh: Setup a Brev instance for Ministral optimization

# Install vLLM for high-throughput serving
pip install vllm mistral-common weave


# Login to W&B if needed
# brew login ... (handled via env vars usually)

echo "Brev instance setup complete for Ministral."
