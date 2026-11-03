#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODEL_DIR="$ROOT/assets/models"
MODEL="$MODEL_DIR/Qwen3-4B-Q4_K_M.gguf"
URL="https://huggingface.co/Qwen/Qwen3-4B-GGUF/resolve/main/Qwen3-4B-Q4_K_M.gguf?download=true"
mkdir -p "$MODEL_DIR"
if [[ -s "$MODEL" ]]; then
  echo "Модель уже есть: $MODEL"
  exit 0
fi
command -v curl >/dev/null || { echo "Нужен curl" >&2; exit 1; }
echo "Скачиваю Qwen3-4B Q4_K_M (~2,5 ГБ). Не прерывай загрузку."
curl -L --fail --retry 5 --retry-delay 3 --continue-at - "$URL" -o "$MODEL"
SIZE=$(stat -c%s "$MODEL" 2>/dev/null || stat -f%z "$MODEL")
if [[ "$SIZE" -lt 2000000000 ]]; then
  echo "Файл подозрительно мал ($SIZE байт); удаляю неполную загрузку." >&2
  rm -f "$MODEL"
  exit 2
fi
echo "Модель загружена: $MODEL"
