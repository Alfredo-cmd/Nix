import os
import subprocess
import tempfile
from pathlib import Path

from voice.local_tts import speak as local_speak
from voice.recorder import record_audio
from voice.stt import transcribe
from voice.tts import synthesize


class VoiceAssistant:
    """Interface de voz da Nix: STT -> Agent -> Qwen TTS."""

    def __init__(self, agent):
        self.agent = agent
        self.tts_enabled = os.getenv("VOICE_TTS_ENABLED", "true").lower() == "true"
        self.local_fallback = os.getenv("VOICE_TTS_FALLBACK", "true").lower() == "true"

    def run(self):
        print()
        print("╭──────────────────────────────────╮")
        print("│           NIX - MODO VOZ         │")
        print("╰──────────────────────────────────╯")
        print()
        print("Pressione ENTER para falar.")
        print("Digite Ctrl+C para sair.")
        print("Voz principal: Qwen3-TTS local")

        while True:
            try:
                input("\nPressione ENTER para começar...")

                print("🎙️  Ouvindo...")

                with tempfile.TemporaryDirectory() as temp_dir:
                    audio_path = Path(temp_dir) / "input.wav"

                    record_audio(str(audio_path))

                    print("🧠 Transcrevendo...")
                    text = transcribe(str(audio_path)).strip()

                if not text:
                    print("[VOICE] Nenhuma fala detectada.")
                    continue

                print(f"Você: {text}")

                if text.lower() in {"sair", "exit", "quit"}:
                    print("Até mais.")
                    break

                print("🤖 Nix pensando...")
                response = self.agent.process(text)

                model_info = self.agent.llm.get_last_model()
                if model_info:
                    print(
                        "Nix "
                        f"[{model_info['provider']} • {model_info['model']}]"
                    )
                else:
                    print("Nix")

                print(response)

                if self.tts_enabled:
                    print("🔊 Nix falando...")
                    self._speak(response)

            except KeyboardInterrupt:
                print("\nAté mais.")
                break

            except Exception as error:
                print(f"\n[VOICE] Erro: {error}")

    def _speak(self, text: str):
        if not text or not text.strip():
            return

        try:
            # O arquivo é temporário: não polui a raiz do projeto.
            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = Path(temp_dir) / "nix.wav"
                synthesize(text, str(output_path))
                self._play_audio(output_path)

        except Exception as error:
            print(f"[VOICE] Qwen TTS falhou: {error}")

            if not self.local_fallback:
                print("[VOICE] Fallback local está desativado.")
                return

            print("[VOICE] Usando TTS local como fallback.")
            local_speak(text)

    @staticmethod
    def _play_audio(audio_path: Path):
        subprocess.run(
            ["pw-play", str(audio_path)],
            check=True,
        )
