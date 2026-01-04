#!/bin/bash
# Example: Building with hardware-specific optimizations

# Detect hardware and optimize
ARCH=$(uname -m)

if [ "$ARCH" = "x86_64" ]; then
    export TENSOR_ACCEL="avx2,avx512"
    export GGML_BACKEND="cpu,gpu"
elif [ "$ARCH" = "aarch64" ]; then
    export TENSOR_ACCEL="neon"
    export GGML_BACKEND="cpu"
fi

./foundation-build.sh
