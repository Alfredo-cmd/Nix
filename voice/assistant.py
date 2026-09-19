import os
import subprocess
import tempfile
from pathlib import Path

from voice.recorder import record_audio
from voice.stt import transcribe
from voice.tts_queue import TTSQueue
from voice.tts_router import TTSRouter


# Frases exibidas no terminal quando uma ferramenta REALMENTE começa.
# Elas não são enviadas para o TTS.
TOOL_PROGRESS_PHRASES = {
    "get_system_info": "Beleza, vou verificar o sistema.",
    "list_directory": "Vou dar uma olhada na pasta.",
    "list_directory_recursive": "Vou explorar as pastas.",
    "read_file": "Vou ler o arquivo.",
    "write_file": "Vou escrever o arquivo.",
}

DEFAULT_PROGRESS_PHRASE = "Beleza, vou verificar isso."


class VoiceAssistant:
    """Interface de voz da Nix: STT -> Agent -> TTS."""

    def __init__(self, agent):
        self.agent = agent

        self.tts_enabled = (
            os.getenv("VOICE_TTS_ENABLED", "true").lower() == "true"
        )

        self._router = TTSRouter(
            play_fn=self._play_audio
        )

        self._tts_queue = TTSQueue(
            speak_fn=self._router.speak
        )

    def run(self):
        print()
        print("╭──────────────────────────────────╮")
        print("│           NIX - MODO VOZ         │")
        print("╰──────────────────────────────────╯")
        print()
        print("Pressione ENTER para falar.")
        print("A Nix só aceitará a próxima fala quando terminar de responder.")
        print("Digite Ctrl+C para sair.")
        print("Voz principal: Kokoro PT-BR")

        try:
            while True:
                try:
                    self._interaction()

                except KeyboardInterrupt:
                    print("\nAté mais.")
                    break

                except Exception as error:
                    print(f"\n[VOICE] Erro: {error}")

        finally:
            print("\n[VOICE] Encerrando voz...")
            self._tts_queue.stop(wait=True)
            print("[VOICE] Modo voz encerrado.")

    def _interaction(self):
        input("\nPressione ENTER para começar...")

        print("🎙️  Ouvindo...")

        with tempfile.TemporaryDirectory() as temp_dir:
            audio_path = Path(temp_dir) / "input.wav"

            record_audio(str(audio_path))

            print("🧠 Transcrevendo...")

            text = transcribe(
                str(audio_path)
            ).strip()

        if not text:
            print("[VOICE] Nenhuma fala detectada.")
            return

        print(f"Você: {text}")

        if text.lower() in {"sair", "exit", "quit"}:
            print("Até mais.")
            raise KeyboardInterrupt

        print("🤖 Nix pensando...")

        response = self.agent.process(
            text,
            on_event=self._on_event,
            voice_mode=True,
        )

        model_info = self.agent.llm.get_last_model()

        if model_info:
            print(
                "Nix "
                f"[{model_info['provider']} • "
                f"{model_info['model']}]"
            )
        else:
            print("Nix")

        print(response)

        # Somente a resposta final é enviada para o TTS.
        # Eventos de ferramentas NÃO são falados.
        if self.tts_enabled:
            self._tts_queue.enqueue(
                response,
                kind="response",
            )

            # Aguarda a fala terminar antes de aceitar outra interação.
            self._tts_queue.wait_until_idle()

    def _on_event(self, event):
        """
        Recebe eventos REAIS do Agent/ToolManager.

        Os eventos são exibidos no terminal apenas para acompanhamento.
        Eles NÃO são enviados para o TTS.
        """

        if event.get("type") != "TOOL_STARTED":
            return

        tool = event.get("tool")

        phrase = TOOL_PROGRESS_PHRASES.get(
            tool,
            DEFAULT_PROGRESS_PHRASE,
        )

        print(f"⏳ {phrase}")

    @staticmethod
    def _play_audio(audio_path: Path):
        process = subprocess.Popen(
            ["pw-play", str(audio_path)]
        )

        try:
            process.wait()

        except KeyboardInterrupt:
            process.terminate()

            try:
                process.wait(timeout=2)

            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

            raise