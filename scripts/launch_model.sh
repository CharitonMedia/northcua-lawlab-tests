#!/usr/bin/env bash
set -euo pipefail
# Run on the GPU host with the two independently hashed model files.
: "${MODEL_DIR:?Set MODEL_DIR to the downloaded NorthCUA-Nano GGUF directory}"
GPU_INDEX="${GPU_INDEX:-0}"
test "$(nvidia-smi -i "$GPU_INDEX" --query-gpu=name --format=csv,noheader)" = "NVIDIA GeForce RTX 3090"
docker run -d --name northcua-nano-3090-test --gpus "\"device=$GPU_INDEX\"" \
 --restart no -p 127.0.0.1:19093:8080 -v "$MODEL_DIR:/models:ro" \
 ghcr.io/ggml-org/llama.cpp:server-cuda@sha256:a8cf841eef4e9d6ea28bb4d88eea1004032a2bf0d1302bff7b8d2100e801ed16 \
 -m /models/NorthCUA-Nano.Q8_0.gguf --mmproj /models/NorthCUA-Nano.mmproj-f16.gguf \
 --alias northcua-nano -ngl 99 -c 131072 -np 1 -t 16 -b 512 -ub 128 \
 --jinja --flash-attn on --cache-type-k q8_0 --cache-type-v q8_0 \
 --host 0.0.0.0 --port 8080
