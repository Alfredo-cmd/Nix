"""Kokoro TTS para a Nix."""

import os
import re
import time
from pathlib import Path

import numpy as np
import soundfile as sf

from kokoro import KPipeline


LANG_CODE = os.getenv("KOKORO_LANG", "p")
VOICE = os.getenv("KOKORO_VOICE", "pf_dora")

_pipeline = None


def _load_pipeline():
    global _pipeline

    if _pipeline is not None:
        return _pipeline

    print("[TTS] Carregando Kokoro...")
    start = time.perf_counter()

    _pipeline = KPipeline(lang_code=LANG_CODE)

    elapsed = time.perf_counter() - start
    print(f"[TTS] Modelo carregado: {elapsed:.1f}s")

    return _pipeline


def prepare_for_speech(text: str) -> str:
    text = text.strip()

    text = re.sub(
        r"```.*?```",
        "",
        text,
        flags=re.DOTALL,
    )

    text = re.sub(
        r"\[([^\]]+)\]\([^)]*\)",
        r"\1",
        text,
    )

    text = re.sub(
        r"^\s*#{1,6}\s*",
        "",
        text,
        flags=re.MULTILINE,
    )

    text = re.sub(
        r"^\s*[-*+]\s+",
        "",
        text,
        flags=re.MULTILINE,
    )

    text = re.sub(
        r"^\s*\d+[.)]\s+",
        "",
        text,
        flags=re.MULTILINE,
    )

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def synthesize(text: str, output_path: str, metrics_callback=None):
    total_start = time.perf_counter()

    text = prepare_for_speech(text)

    if not text:
        raise ValueError("O texto para síntese ficou vazio.")

    pipeline = _load_pipeline()

    output = Path(output_path).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)

    print("[TTS] Gerando fala...")

    generate_start = time.perf_counter()

    chunks = []

    for _, _, audio in pipeline(
        text,
        voice=VOICE,
    ):
        chunks.append(audio)

    generate_elapsed = time.perf_counter() - generate_start

    if not chunks:
        raise RuntimeError("O Kokoro não retornou áudio.")

    audio = np.concatenate(chunks)

    sample_rate = 24000

    sf.write(
        output,
        audio,
        sample_rate,
    )

    if not output.exists() or output.stat().st_size == 0:
        raise RuntimeError(
            "O Kokoro não criou um arquivo de áudio válido."
        )

    duration = len(audio) / sample_rate
    realtime_factor = (
        generate_elapsed / duration
        if duration > 0
        else 0
    )

    total_elapsed = time.perf_counter() - total_start

    print(f"[TTS] Gerando áudio: {generate_elapsed:.1f}s")
    print(f"[TTS] Duração: {duration:.1f}s")
    print(f"[TTS] Fator tempo real: {realtime_factor:.2f}x")
    print(f"[TTS] Síntese total: {total_elapsed:.1f}s")

    if metrics_callback:
        try:
            metrics_callback({
                "gerando_audio_s": generate_elapsed,
                "sintese_total_s": total_elapsed,
                "audio_duration_s": duration,
                "realtime_factor": realtime_factor,
            })
        except Exception:
            pass

    return str(output)