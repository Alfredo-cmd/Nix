from pathlib import Path

import soundfile as sf
import torch

from qwen_tts import Qwen3TTSModel


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REFERENCE_AUDIO = PROJECT_ROOT / "voice" / "sample.wav"

MODEL_ID = "Qwen/Qwen3-TTS-12Hz-0.6B-Base"

_model = None
_voice_clone_prompt = None


def _load_model():
    global _model

    if _model is not None:
        return _model

    print("Carregando Qwen3-TTS 0.6B...")

    _model = Qwen3TTSModel.from_pretrained(
        MODEL_ID,
        device_map="cpu",
        dtype=torch.float32,
        attn_implementation="sdpa",
    )

    return _model


def _load_voice():
    global _voice_clone_prompt

    if _voice_clone_prompt is not None:
        return _voice_clone_prompt

    if not REFERENCE_AUDIO.exists():
        raise FileNotFoundError(
            f"Áudio de referência não encontrado: {REFERENCE_AUDIO}"
        )

    model = _load_model()

    print("Preparando a voz da Nix...")

    reference_text = (
        "Olá. Eu sou a Nix, sua assistente pessoal."
    )

    _voice_clone_prompt = model.create_voice_clone_prompt(
        ref_audio=str(REFERENCE_AUDIO),
        ref_text=reference_text,
        x_vector_only_mode=False,
    )

    return _voice_clone_prompt


def synthesize(text: str, output_path: str):
    if not text or not text.strip():
        raise ValueError("O texto para síntese está vazio.")

    model = _load_model()
    voice_prompt = _load_voice()

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    print("Gerando áudio...")

    wavs, sample_rate = model.generate_voice_clone(
        text=text,
        language="Portuguese",
        voice_clone_prompt=voice_prompt,
    )

    sf.write(output, wavs[0], sample_rate)

    return str(output)