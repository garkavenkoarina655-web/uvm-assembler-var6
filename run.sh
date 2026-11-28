#!/usr/bin/env bash
# Скрипт запуска ассемблера / интерпретатора УВМ
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 assemble <source.json> <output.bin> [--test]"
  echo "       $0 interpret <program.bin> <dump.csv> <start> <end>"
  exit 1
fi

cmd="$1"
shift

case "$cmd" in
  assemble)
    python3 "$ROOT/src/assembler.py" "$@"
    ;;
  *)
    echo "Unknown command: $cmd"
    exit 1
    ;;
esac
