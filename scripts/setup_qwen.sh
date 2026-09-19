#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

if [[ ! -d .qwen-venv ]]; then
    python3.12 -m venv .qwen-venv
fi

source .qwen-venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-qwen.txt

cat <<'MSG'

Ambiente Qwen preparado.

Para testar:
  source .qwen-venv/bin/activate
  python tools/test_qwen_tts.py

Para iniciar a Nix com voz:
  python main.py --voice
MSG
