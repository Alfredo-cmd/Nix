import tempfile
import time
from pathlib import Path

from voice.tts import synthesize


class TTSRouter:
    def __init__(self, play_fn):
        self._play_fn = play_fn

    def speak(self, text, kind="response"):
        self._speak_kokoro(text)

    def _speak_kokoro(self, text):
        metrics = {}

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "nix.wav"

            synthesize(
                text,
                str(output_path),
                metrics_callback=metrics.update,
            )

            play_start = time.perf_counter()

            self._play_fn(output_path)

            play_elapsed = time.perf_counter() - play_start

            print(f"[TTS] Reprodução: {play_elapsed:.1f}s")

            total = (
                metrics.get("sintese_total_s", 0)
                + play_elapsed
            )

            print(f"[TTS] Total: {total:.1f}s")