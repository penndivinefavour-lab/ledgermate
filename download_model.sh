#!/usr/bin/env bash
set -euo pipefail

MODEL_DIR="model"
mkdir -p "$MODEL_DIR"

# Verified public GGUF source: hugging-quants/Llama-3.2-1B-Instruct-Q4_K_M-GGUF
# Base model: meta-llama/Llama-3.2-1B-Instruct
# License: Llama 3.2 Community License
MODEL_URL="https://huggingface.co/hugging-quants/Llama-3.2-1B-Instruct-Q4_K_M-GGUF/resolve/main/llama-3.2-1b-instruct-q4_k_m.gguf"
MODEL_FILE="$MODEL_DIR/llama-3.2-1b-instruct-q4_k_m.gguf"

if [ -f "$MODEL_FILE" ]; then
  echo "Model already present: $MODEL_FILE"
  exit 0
fi

echo "Downloading $MODEL_URL ..."
curl -fL --retry 3 --retry-delay 5 -o "$MODEL_FILE" "$MODEL_URL"
echo "Downloaded to $MODEL_FILE"
echo "Verifying file..."
test -s "$MODEL_FILE"
echo "Model file ready."
