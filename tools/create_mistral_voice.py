import base64
import os
from pathlib import Path

import requests

from config.env import load_environment


API_URL = "https://api.mistral.ai/v1/audio/voices"


def main():
    load_environment()

    api_key = os.getenv("MISTRAL_API_KEY")

    if not api_key:
        print("Erro: MISTRAL_API_KEY não configurada.")
        return

    sample_path = Path("voice/sample.wav")

    if not sample_path.exists():
        print(f"Erro: arquivo não encontrado: {sample_path}")
        return

    print("Lendo amostra de voz...")

    audio_base64 = base64.b64encode(
        sample_path.read_bytes()
    ).decode("utf-8")

    payload = {
        "name": "Nix PT-BR",
        "sample_audio": audio_base64,
        "sample_filename": sample_path.name,
        "languages": ["pt"],
        "tags": ["pt-br", "nix"],
    }

    print("Enviando voz para a Mistral...")

    response = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=60,
    )

    if not response.ok:
        print("Erro ao criar voz:")
        print(response.status_code)
        print(response.text)
        return

    data = response.json()

    print()
    print("Voz criada com sucesso!")
    print(f"Nome: {data.get('name')}")
    print(f"ID: {data.get('id')}")
    print(f"Idiomas: {data.get('languages')}")


if __name__ == "__main__":
    main()
