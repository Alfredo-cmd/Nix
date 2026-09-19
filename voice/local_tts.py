import subprocess
from pathlib import Path


def speak(text: str):
    """
    Fallback local usando espeak-ng.

    Não é nossa voz final, mas permite testar TTS
    sem depender de uma API.
    """

    if not text.strip():
        return

    try:
        subprocess.run(
            [
                "espeak-ng",
                "-v",
                "pt-br",
                "-s",
                "155",
                text
            ],
            check=True
        )

    except FileNotFoundError as error:
        raise RuntimeError(
            "espeak-ng não está instalado."
        ) from error

    except subprocess.CalledProcessError as error:
        raise RuntimeError(
            "espeak-ng falhou."
        ) from error