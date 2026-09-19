import subprocess
from pathlib import Path


SAMPLE_RATE = 16000
CHANNELS = 1
DURATION = 6


def record_audio(output_path: str):
    """
    Grava áudio pelo PipeWire.

    A gravação é limitada a alguns segundos para manter
    o teste simples. Depois podemos substituir isso por
    VAD para detectar automaticamente início e fim da fala.
    """

    path = Path(output_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    command = [
        "pw-record",
        "--rate",
        str(SAMPLE_RATE),
        "--channels",
        str(CHANNELS),
        "--format",
        "s16",
        "--target",
        "@DEFAULT_AUDIO_SOURCE@",
        str(path)
    ]

    process = subprocess.Popen(
        command
    )

    try:
        process.wait(
            timeout=DURATION
        )

    except subprocess.TimeoutExpired:
        process.terminate()

        try:
            process.wait(
                timeout=2
            )
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

    if process.returncode not in [
        0,
        -15
    ]:
        raise RuntimeError(
            f"pw-record terminou com código "
            f"{process.returncode}"
        )

    if not path.exists():
        raise RuntimeError(
            "O arquivo de áudio não foi criado."
        )

    if path.stat().st_size == 0:
        raise RuntimeError(
            "O arquivo de áudio ficou vazio."
        )