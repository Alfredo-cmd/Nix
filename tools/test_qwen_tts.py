from pathlib import Path

import soundfile as sf
import torch

from qwen_tts import Qwen3TTSModel


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REFERENCE_AUDIO = PROJECT_ROOT / "voice" / "sample.wav"
OUTPUT_AUDIO = PROJECT_ROOT / "voice" / "qwen_test.wav"

MODEL_ID = "Qwen/Qwen3-TTS-12Hz-0.6B-Base"


def main():
    if not REFERENCE_AUDIO.exists():
        print(f"Erro: arquivo não encontrado: {REFERENCE_AUDIO}")
        return

    print("======================================")
    print(" Qwen3-TTS 0.6B — teste de voz")
    print("======================================")
    print(f"Áudio de referência: {REFERENCE_AUDIO}")
    print(f"GPU disponível: {torch.cuda.is_available()}")
    print()
    print("Carregando modelo...")
    print("Na primeira execução, os arquivos serão baixados.")
    print()

    model = Qwen3TTSModel.from_pretrained(
        MODEL_ID,
        device_map="cpu",
        dtype=torch.float32,
        attn_implementation="sdpa",
    )

    print("Modelo carregado.")
    print("Gerando voz...")
    print()

    ref_text = "Olá. Eu sou a Nix, sua assistente pessoal."

    text = (
        "Olá! Eu sou a Nix, sua assistente pessoal. "
        "Este é um teste da minha voz. "
        "Estou rodando localmente no seu computador."
    )

    wavs, sample_rate = model.generate_voice_clone(
        text=text,
        language="Portuguese",
        ref_audio=str(REFERENCE_AUDIO),
        ref_text=ref_text,
    )

    sf.write(OUTPUT_AUDIO, wavs[0], sample_rate)

    print()
    print("======================================")
    print(" Áudio gerado com sucesso!")
    print("======================================")
    print(f"Arquivo: {OUTPUT_AUDIO}")
    print(f"Sample rate: {sample_rate} Hz")


if __name__ == "__main__":
    main()
