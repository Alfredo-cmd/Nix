import os
import tempfile
from pathlib import Path

from voice.recorder import record_audio
from voice.stt import transcribe
from voice.tts import synthesize
from voice.local_tts import speak as local_speak


class VoiceAssistant:

    def __init__(self, agent):
        self.agent = agent

    def run(self):
        print()
        print("╭──────────────────────────────────╮")
        print("│           NIX - MODO VOZ          │")
        print("╰──────────────────────────────────╯")
        print()
        print("Pressione ENTER para falar.")
        print("Digite Ctrl+C para sair.")

        while True:
            try:
                input("\nPressione ENTER para começar...")

                print("🎙️  Ouvindo...")

                with tempfile.TemporaryDirectory() as temp_dir:

                    audio_path = Path(
                        temp_dir
                    ) / "input.wav"

                    record_audio(
                        str(audio_path)
                    )

                    print("🧠 Transcrevendo...")

                    text = transcribe(
                        str(audio_path)
                    )

                    print(f"Você: {text}")

                    if text.lower() in [
                        "sair",
                        "exit",
                        "quit"
                    ]:
                        print("Até mais.")
                        break

                    print("🤖 Nix pensando...")

                    response = self.agent.process(
                        text
                    )

                    model_info = (
                        self.agent
                        .llm
                        .get_last_model()
                    )

                    if model_info:
                        print(
                            "Nix "
                            f"[{model_info['provider']} • "
                            f"{model_info['model']}]"
                        )
                    else:
                        print("Nix")

                    print(response)

                    print("🔊 Falando...")

                    self._speak(response)

            except KeyboardInterrupt:
                print("\nAté mais.")
                break

            except Exception as error:
                print(
                    f"\n[VOICE] Erro: {error}"
                )

    def _speak(self, text):
        output_path = Path(
            "voice_output.wav"
        )

        try:
            synthesize(
                text,
                str(output_path)
            )

            self._play_audio(
                output_path
            )

        except Exception as error:
            print(
                f"[VOICE] Mistral TTS falhou: {error}"
            )

            print(
                "[VOICE] Usando TTS local."
            )

            local_speak(text)

    def _play_audio(self, audio_path):
        import subprocess

        subprocess.run(
            [
                "pw-play",
                str(audio_path)
            ],
            check=True
        )