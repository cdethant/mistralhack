#!/bin/bash
# quantize.sh: Convert Ministral-8B weights to GGUF format for local laptop inference.
# Run this on the Brev instance AFTER evaluations pass in run_eval.py.
#
# Output: A ~5GB Q4_K_M .gguf file you can "siphon" (scp) to your laptop.

set -e

MODEL_HF="mistralai/Ministral-8B-Instruct-2410"
MODEL_DIR="./models/ministral-8b-hf"
OUTPUT_DIR="./models/ministral-8b-gguf"
QUANT_TYPE="Q4_K_M"  # Best quality/size tradeoff for local inference

echo "--- Step 1: Install llama.cpp conversion dependencies ---"
pip install -q transformers huggingface_hub sentencepiece

echo "--- Step 2: Download HF weights (skip if already cached by serve.sh) ---"
mkdir -p "$MODEL_DIR"
python3 - <<'EOF'
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id="mistralai/Ministral-8B-Instruct-2410",
    local_dir="./models/ministral-8b-hf"
)
print("Model downloaded.")
EOF

echo "--- Step 3: Clone llama.cpp (for conversion tools) ---"
if [ ! -d "llama.cpp" ]; then
    git clone --depth 1 https://github.com/ggerganov/llama.cpp.git
fi
pip install -q -r llama.cpp/requirements.txt

echo "--- Step 4: Convert to GGUF (float16 base) ---"
mkdir -p "$OUTPUT_DIR"
python3 llama.cpp/convert_hf_to_gguf.py "$MODEL_DIR" \
    --outtype f16 \
    --outfile "$OUTPUT_DIR/ministral-8b-f16.gguf"

echo "--- Step 5: Quantize to ${QUANT_TYPE} ---"
# Compile quantize tool if not already built (CPU-only for portability)
if [ ! -f "llama.cpp/llama-quantize" ]; then
    sudo apt-get update && sudo apt-get install -y cmake
    cmake llama.cpp -B llama.cpp/build -DGGML_CUDA=OFF
    cmake --build llama.cpp/build --config Release -j$(nproc) --target llama-quantize
    cp llama.cpp/build/bin/llama-quantize llama.cpp/
fi

llama.cpp/llama-quantize \
    "$OUTPUT_DIR/ministral-8b-f16.gguf" \
    "$OUTPUT_DIR/ministral-8b-${QUANT_TYPE}.gguf" \
    "$QUANT_TYPE"

echo ""
echo "✅ Quantization complete!"
echo "Output: $OUTPUT_DIR/ministral-8b-${QUANT_TYPE}.gguf"
echo "Size: $(du -sh $OUTPUT_DIR/ministral-8b-${QUANT_TYPE}.gguf | cut -f1)"
echo ""
echo "➡️  Run brev/siphon.sh on your LOCAL laptop to download this file."
