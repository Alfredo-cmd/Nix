# Nix

Assistente pessoal de IA para NixOS/Linux, com ferramentas de sistema, múltiplos provedores de LLM e interface de voz.

## Personalidade

O Nix responde de forma direta e natural, evitando textos longos e frases
artificiais de IA ("Como uma inteligência artificial...", "Estou aqui para
ajudá-lo..."). As regras de tom e concisão ficam em `config/personality.py`.

No **modo voz**, um adendo extra (`VOICE_MODE_ADDENDUM`) é somado ao prompt
de sistema pedindo respostas ainda mais curtas, já que todo texto passa
pelo TTS antes de ser ouvido.

## Progresso durante tarefas

O `ToolManager` emite eventos reais de progresso (`TOOL_STARTED` /
`TOOL_FINISHED`) exatamente quando uma ferramenta é executada de verdade —
nunca antes, nunca de forma inventada. O `Agent.process()` aceita um
callback `on_event` opcional; o modo texto usa isso para imprimir uma linha
curta ("… executando get_system_info") e o modo voz usa para falar uma
frase curta com o backend rápido de TTS enquanto a ferramenta roda.

## Voz

O modo de voz usa:

1. `pw-record` para gravar;
2. Groq Whisper para STT;
3. o mesmo `Agent` usado no modo texto (com `voice_mode=True`, prompt mais
   curto, e eventos de progresso reais);
4. um **TTS Router** (`voice/tts_router.py`) que escolhe entre o Qwen3-TTS
   (voz clonada, alta qualidade) e um backend rápido (`espeak-ng`) para a
   resposta final, com fallback automático se o Qwen falhar;
5. uma **fila assíncrona de TTS** (`voice/tts_queue.py`) que fala em uma
   thread separada, sem travar o assistente esperando o áudio terminar;
6. `pw-play` para reproduzir.

O modelo Qwen e o prompt de clonagem ficam carregados em memória depois da
primeira fala, evitando recarregar o modelo a cada resposta.

### Progresso falado

Mensagens de progresso ("Beleza, vou verificar o sistema.") **sempre**
usam o backend rápido (`espeak-ng`), mesmo quando a resposta final usa o
Qwen — não faz sentido esperar 40s de Qwen só para anunciar que uma
verificação está começando. A fila descarta mensagens de progresso antigas
que ainda não foram faladas quando uma nova chega, para não acumular
"estou verificando... estou analisando..." minutos depois de tudo já ter
terminado. A resposta final nunca é descartada.

### Otimizações do Qwen3-TTS (CPU)

- Modelo e voice-clone-prompt ficam em memória (globals com lazy-load), só
  são recriados uma vez por processo.
- Geração e criação do voice-clone-prompt rodam dentro de
  `torch.inference_mode()`.
- `model.eval()` é chamado após o carregamento, quando suportado.
- `QWEN_TTS_THREADS` permite testar um número fixo de threads de CPU do
  PyTorch (vazio = padrão do PyTorch). Em CPUs modestas (ex.: Ryzen 5
  3500U, 4 núcleos), vale experimentar valores como `4`.
- Métricas de tempo são impressas a cada síntese:
  `[TTS] Carregando modelo`, `[TTS] Preparando voz`, `[TTS] Gerando áudio`,
  `[TTS] Reprodução`, `[TTS] Total`.
- **Nada disso usa CUDA por padrão.** `QWEN_TTS_DEVICE=auto` só usa CUDA se
  `torch.cuda.is_available()` for verdadeiro; o padrão continua sendo CPU.

Se, mesmo com essas otimizações, o Qwen continuar impraticável no seu
hardware, defina `VOICE_TTS_BACKEND=fast` no `.env` para usar sempre o
backend leve na resposta final (a arquitetura de TTS Router já está
preparada para isso).

### Requisito importante

O arquivo `voice/sample.wav` é a amostra usada para clonar a voz. Ele é
propositalmente ignorado pelo Git porque o repositório é público. Mantenha
esse arquivo somente na máquina local.

### Ambiente Qwen

O projeto possui um `shell-qwen.nix` para preparar o ambiente Nix. O
ambiente virtual local recomendado é `.qwen-venv/`.

Depois de entrar no ambiente que contém `qwen-tts`, `torch` e `soundfile`,
teste:

```bash
python tools/test_qwen_tts.py
```

Depois rode o assistente:

```bash
python main.py --voice
```

Se o Qwen falhar, o assistente pode usar `espeak-ng` como fallback quando
`VOICE_TTS_FALLBACK=true`.

## Streaming (preparação)

`llm/gateway.py` tem um método `chat_stream()` que já sabe conversar em
streaming com o OpenRouter (chamada com `stream=True`, processando os
chunks SSE). Ele ainda **não é usado** pelo fluxo principal — não trata
`tool_calls` em streaming — e existe como base para, no futuro, o Nix
começar a falar a primeira frase da resposta antes do restante terminar
de ser gerado. Ver seção "TTS assíncrono" acima para o desenho geral.

## Segurança

Nunca versione `.env`, tokens de API, `.qwen-venv`, `.hf-cache` ou a
amostra de voz pessoal.
