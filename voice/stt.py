import os
from pathlib import Path

import requests


GROQ_URL = (
    "https://api.groq.com/openai/v1/audio/transcriptions"
)

GROQ_MODEL = os.getenv(
    "GROQ_STT_MODEL",
    "whisper-large-v3"
)


def transcribe(audio_path: str) -> str:
    """
    Converte um arquivo de áudio em texto usando Groq Whisper.
    """

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY não configurada."
        )

    path = Path(audio_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Áudio não encontrado: {path}"
        )

    try:
        with open(path, "rb") as audio_file:
            response = requests.post(
                GROQ_URL,
                headers={
                    "Authorization": (
                        f"Bearer {api_key}"
                    )
                },
                files={
                    "file": (
                        path.name,
                        audio_file,
                        "audio/wav"
                    )
                },
                data={
                    "model": GROQ_MODEL,
                    "language": "pt",
                    "response_format": "json",
                    "temperature": "0",
                    "prompt": (
                        "Português brasileiro. "
                        "Nix, NixOS, Linux, Python, "
                        "KDE Plasma, AMD Ryzen, Radeon."
                    )
                },
                timeout=60
            )

        response.raise_for_status()

        data = response.json()

        text = data.get("text", "").strip()

        if not text:
            raise RuntimeError(
                "O STT não retornou nenhum texto."
            )

        return text

    except requests.RequestException as error:
        raise RuntimeError(
            f"Erro na API de transcrição: {error}"
        ) from error