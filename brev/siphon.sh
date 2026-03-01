#!/bin/bash
# siphon.sh: Download the quantized GGUF model from the Brev instance to your local laptop.
# Run this on your LOCAL MACHINE after quantize.sh completes on Brev.

set -e

BREV_INSTANCE="optiministral"  # Set via env or default
REMOTE_GGUF_PATH="~/mistralhack/models/ministral-8b-gguf/ministral-8b-Q4_K_M.gguf"
LOCAL_MODEL_DIR="./models"

echo "--- Siphoning quantized model from Brev: $BREV_INSTANCE ---"
echo "    This is a ~5GB file. Estimated time depends on your connection."
echo ""

mkdir -p "$LOCAL_MODEL_DIR"

rsync -avP "$BREV_INSTANCE:$REMOTE_GGUF_PATH" "$LOCAL_MODEL_DIR"

echo ""
echo "Model siphoned to $LOCAL_MODEL_DIR"
echo "Size: $(du -sh $LOCAL_MODEL_DIR | cut -f1)"
echo ""
echo "Now run: bash local/serve.sh"
