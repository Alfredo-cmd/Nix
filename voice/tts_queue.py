import threading


class TTSQueue:
    """Fila de fala síncrona com prioridade para a resposta final."""

    def __init__(self, speak_fn):
        self._speak_fn = speak_fn
        self._items = []
        self._cond = threading.Condition()
        self._stop_flag = False
        self._speaking = False

        self._thread = threading.Thread(
            target=self._worker,
            daemon=True,
        )
        self._thread.start()

    def enqueue(self, text, kind="response"):
        if not text or not text.strip():
            return

        with self._cond:
            if self._stop_flag:
                return

            if kind == "progress":
                # Só mantém o progresso mais recente.
                self._items = [
                    item
                    for item in self._items
                    if item["kind"] != "progress"
                ]

            elif kind == "response":
                # A resposta final tem prioridade.
                self._items = [
                    item
                    for item in self._items
                    if item["kind"] != "response"
                ]

                # Progresso antigo não deve ser falado depois
                # da resposta final.
                self._items = [
                    item
                    for item in self._items
                    if item["kind"] != "progress"
                ]

            self._items.append({
                "text": text.strip(),
                "kind": kind,
            })

            self._cond.notify_all()

    def wait_until_idle(self, timeout=None):
        """Espera até a fila terminar de falar."""
        with self._cond:
            if timeout is None:
                while self._speaking or self._items:
                    self._cond.wait()
                return True

            import time

            deadline = time.monotonic() + timeout

            while self._speaking or self._items:
                remaining = deadline - time.monotonic()

                if remaining <= 0:
                    return False

                self._cond.wait(timeout=remaining)

            return True

    def _worker(self):
        while True:
            with self._cond:
                while not self._items and not self._stop_flag:
                    self._cond.wait()

                if self._stop_flag:
                    self._items.clear()
                    self._speaking = False
                    self._cond.notify_all()
                    return

                item = self._items.pop(0)
                self._speaking = True

            try:
                self._speak_fn(
                    item["text"],
                    item["kind"],
                )

            except Exception as error:
                print(f"[TTS] Erro na fala: {error}")

            finally:
                with self._cond:
                    self._speaking = False
                    self._cond.notify_all()

    def stop(self, wait=False):
        with self._cond:
            self._stop_flag = True
            self._items.clear()
            self._cond.notify_all()

        if wait:
            self._thread.join(timeout=10)

    @property
    def speaking(self):
        with self._cond:
            return self._speaking

    @property
    def pending(self):
        with self._cond:
            return len(self._items)