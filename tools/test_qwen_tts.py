from pathlib import Path

from voice.tts import synthesize


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_AUDIO = PROJECT_ROOT / "voice" / "qwen_test.wav"


def main():
    print("======================================")
    print(" Nix — teste do Qwen3-TTS")
    print("======================================")

    text = (
        "Olá! Eu sou a Nix, sua assistente pessoal. "
        "Este é um teste da minha voz local. "
        "Estou usando o Qwen três TTS para gerar esta fala."
    )

    synthesize(text, str(OUTPUT_AUDIO))

    print()
    print(f"Áudio gerado: {OUTPUT_AUDIO}")


if __name__ == "__main__":
    main()
