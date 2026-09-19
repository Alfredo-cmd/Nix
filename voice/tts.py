"""Qwen3-TTS voice synthesis for Nix.

The model and voice-clone prompt are loaded lazily and kept in memory so a
conversation does not reload the model for every sentence.
"""

import os
import re
from pathlib import Path

import soundfile as sf
import torch


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REFERENCE_AUDIO = Path(
    os.getenv(
        "QWEN_TTS_REFERENCE_AUDIO",
        str(PROJECT_ROOT / "voice" / "sample.wav"),
    )
).expanduser()

MODEL_ID = os.getenv(
    "QWEN_TTS_MODEL",
    "Qwen/Qwen3-TTS-12Hz-0.6B-Base",
)
LANGUAGE = os.getenv("QWEN_TTS_LANGUAGE", "Portuguese")
REFERENCE_TEXT = os.getenv(
    "QWEN_TTS_REFERENCE_TEXT",
    "Olá. Eu sou a Nix, sua assistente pessoal.",
)
DEVICE = os.getenv("QWEN_TTS_DEVICE", "cpu").lower()

_model = None
_voice_clone_prompt = None


def _resolve_device() -> str:
    if DEVICE == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"

    if DEVICE == "cuda" and not torch.cuda.is_available():
        print("[TTS] CUDA não está disponível; usando CPU.")
        return "cpu"

    return DEVICE


def _load_model():
    global _model

    if _model is not None:
        return _model

    try:
        from qwen_tts import Qwen3TTSModel
    except ImportError as error:
        raise RuntimeError(
            "Qwen3-TTS não está instalado neste ambiente Python. "
            "Entre no ambiente .qwen-venv antes de iniciar o modo voz."
        ) from error

    device = _resolve_device()

    print("[TTS] Carregando Qwen3-TTS 0.6B...")
    print(f"[TTS] Modelo: {MODEL_ID}")
    print(f"[TTS] Dispositivo: {device}")

    kwargs = {
        "device_map": device,
        "dtype": torch.float32,
        "attn_implementation": "sdpa",
    }

    try:
        _model = Qwen3TTSModel.from_pretrained(
            MODEL_ID,
            **kwargs,
        )
    except Exception as error:
        raise RuntimeError(
            f"Não foi possível carregar o Qwen3-TTS: {error}"
        ) from error

    print("[TTS] Qwen3-TTS carregado.")
    return _model


def _load_voice():
    global _voice_clone_prompt

    if _voice_clone_prompt is not None:
        return _voice_clone_prompt

    if not REFERENCE_AUDIO.exists():
        raise FileNotFoundError(
            "Áudio de referência da Nix não encontrado: "
            f"{REFERENCE_AUDIO}"
        )

    model = _load_model()

    print("[TTS] Preparando a voz clonada da Nix...")

    try:
        _voice_clone_prompt = model.create_voice_clone_prompt(
            ref_audio=str(REFERENCE_AUDIO),
            ref_text=REFERENCE_TEXT,
            x_vector_only_mode=False,
        )
    except Exception as error:
        raise RuntimeError(
            "Não foi possível preparar a voz de referência do Qwen: "
            f"{error}"
        ) from error

    print("[TTS] Voz da Nix preparada.")
    return _voice_clone_prompt


def prepare_for_speech(text: str) -> str:
    """Remove formatação que costuma soar estranha em TTS."""

    text = text.strip()

    # Remove blocos de código inteiros.
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)

    # Markdown links: mantém apenas o texto visível.
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)

    # Remove cabeçalhos e marcadores de lista sem alterar o conteúdo.
    text = re.sub(r"^\s*#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+[.)]\s+", "", text, flags=re.MULTILINE)

    # Evita sequências exageradas de espaços/quebras de linha.
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def synthesize(text: str, output_path: str):
    """Gera um WAV usando a voz clonada da Nix."""

    text = prepare_for_speech(text)

    if not text:
        raise ValueError("O texto para síntese ficou vazio.")

    model = _load_model()
    voice_prompt = _load_voice()

    output = Path(output_path).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)

    print("[TTS] Gerando fala...")

    try:
        wavs, sample_rate = model.generate_voice_clone(
            text=text,
            language=LANGUAGE,
            voice_clone_prompt=voice_prompt,
        )
    except Exception as error:
        raise RuntimeError(
            f"O Qwen3-TTS falhou ao gerar a fala: {error}"
        ) from error

    if not wavs:
        raise RuntimeError("O Qwen3-TTS não retornou áudio.")

    sf.write(output, wavs[0], sample_rate)

    if not output.exists() or output.stat().st_size == 0:
        raise RuntimeError("O Qwen3-TTS não criou um arquivo de áudio válido.")

    return str(output)
