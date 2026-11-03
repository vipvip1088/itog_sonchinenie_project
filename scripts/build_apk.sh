#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODEL="$ROOT/assets/models/Qwen3-4B-Q4_K_M.gguf"
LIB="$ROOT/native/libs/arm64-v8a/libessay_llama.so"
[[ -s "$MODEL" ]] || { echo "Сначала запусти scripts/download_model.sh" >&2; exit 1; }
[[ -s "$LIB" ]] || { echo "Сначала запусти scripts/build_native_android.sh" >&2; exit 1; }
command -v buildozer >/dev/null || { echo "Не найден Buildozer. Установи его в Linux/WSL." >&2; exit 1; }
cd "$ROOT"
buildozer android debug
