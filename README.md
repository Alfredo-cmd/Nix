# Nix

Assistente pessoal de IA para NixOS/Linux, com ferramentas de sistema, múltiplos provedores de LLM e interface de voz.

## Voz

O modo de voz usa:

1. `pw-record` para gravar;
2. Groq Whisper para STT;
3. o mesmo `Agent` usado no modo texto;
4. Qwen3-TTS 0.6B local para sintetizar a resposta;
5. `pw-play` para reproduzir;
6. `espeak-ng` como fallback opcional.

O modelo Qwen e o prompt de clonagem ficam carregados em memória depois da primeira fala, evitando recarregar o modelo a cada resposta.

### Requisito importante

O arquivo `voice/sample.wav` é a amostra usada para clonar a voz. Ele é propositalmente ignorado pelo Git porque o repositório é público. Mantenha esse arquivo somente na máquina local.

### Ambiente Qwen

O projeto possui um `shell-qwen.nix` para preparar o ambiente Nix. O ambiente virtual local recomendado é `.qwen-venv/`.

Depois de entrar no ambiente que contém `qwen-tts`, `torch` e `soundfile`, teste:

```bash
python tools/test_qwen_tts.py
```

Depois rode o assistente:

```bash
python main.py --voice
```

Se o Qwen falhar, o assistente pode usar `espeak-ng` como fallback quando `VOICE_TTS_FALLBACK=true`.

## Segurança

Nunca versione `.env`, tokens de API, `.qwen-venv`, `.hf-cache` ou a amostra de voz pessoal.
