from voice.tts import synthesize


def main():
    output = "voice/nix_integrated_test.wav"

    text = (
        "Olá! Eu sou a Nix. "
        "Agora meu sistema de voz está integrado ao projeto. "
        "Estou utilizando o Qwen3-TTS para reproduzir a voz "
        "com base na amostra configurada."
    )

    synthesize(text, output)

    print()
    print(f"Áudio gerado: {output}")


if __name__ == "__main__":
    main()
