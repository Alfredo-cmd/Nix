import os
import subprocess
from pathlib import Path


SAMPLE_RATE = 16000
CHANNELS = 1
DURATION = max(1, int(os.getenv("VOICE_RECORD_SECONDS", "6")))


def record_audio(output_path: str):
    """
    Grava áudio pelo PipeWire durante alguns segundos.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "pw-record",
        "--rate", str(SAMPLE_RATE),
        "--channels", str(CHANNELS),
        "--format", "s16",
        "--target", "@DEFAULT_AUDIO_SOURCE@",
        str(path),
    ]

    process = subprocess.Popen(command)

    try:
        process.wait(timeout=DURATION)
    except subprocess.TimeoutExpired:
        process.terminate()
        process.wait()

    if not path.exists():
        raise RuntimeError("O arquivo de áudio não foi criado.")

    if path.stat().st_size == 0:
        raise RuntimeError("O arquivo de áudio ficou vazio.")
