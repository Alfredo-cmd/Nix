import json

from core.permissions import PermissionManager
from tools.files import (
    list_directory,
    list_directory_recursive,
    read_file,
    write_file,
)
from tools.system import get_system_info


class ToolManager:

    def __init__(self, confirmation_callback=None):
        self.permissions = PermissionManager()
        self.confirmation_callback = confirmation_callback

        # Callback opcional de eventos de progresso (ex.: TOOL_STARTED,
        # TOOL_FINISHED). É definido pelo LLMGateway durante uma chamada
        # de chat() e emitido apenas quando uma ferramenta REALMENTE é
        # executada — nunca de forma especulativa ou inventada.
        self.event_callback = None

        self.tools = {
            "get_system_info": get_system_info,
            "list_directory": list_directory,
            "list_directory_recursive": list_directory_recursive,
            "read_file": read_file,
            "write_file": write_file,
        }

    def _emit(self, event_type, **data):
        """Emite um evento de progresso real, se houver um callback."""

        if self.event_callback is None:
            return

        try:
            self.event_callback({"type": event_type, **data})
        except Exception as error:
            # Um erro no consumidor de eventos (ex.: TTS) nunca deve
            # interromper a execução real da ferramenta.
            print(f"[EVENTOS] Callback de progresso falhou: {error}")

    def execute(self, name, arguments):
        """Executa uma ferramenta respeitando as permissões."""

        if name not in self.tools:
            return {
                "erro": f"Ferramenta desconhecida: {name}"
            }

        permission = self.permissions.get_permission(name)

        if permission == PermissionManager.BLOCKED:
            return {
                "erro": f"A ferramenta {name} está bloqueada."
            }

        if permission == PermissionManager.CONFIRM:
            if self.confirmation_callback is None:
                return {
                    "erro": (
                        "A ferramenta exige confirmação, "
                        "mas não existe um callback de confirmação."
                    )
                }

            confirmed = self.confirmation_callback(
                name,
                arguments
            )

            if not confirmed:
                return {
                    "cancelado": True,
                    "mensagem": (
                        f"A execução de {name} foi recusada pelo usuário."
                    )
                }

        # A partir daqui a ferramenta VAI rodar de verdade, então o evento
        # de início é genuíno (não é um progresso inventado).
        self._emit("TOOL_STARTED", tool=name, arguments=arguments)

        try:
            result = self.tools[name](**arguments)
            self._emit("TOOL_FINISHED", tool=name, sucesso=True)
            return result
        except Exception as error:
            self._emit("TOOL_FINISHED", tool=name, sucesso=False)
            return {
                "erro": (
                    f"Erro ao executar {name}: {error}"
                )
            }

    def get_gemini_tools(self):
        """Retorna wrappers para o function calling do Gemini."""

        return [
            self._gemini_get_system_info,
            self._gemini_list_directory,
            self._gemini_list_directory_recursive,
            self._gemini_read_file,
            self._gemini_write_file,
        ]

    def _gemini_get_system_info(self):
        """Obtém informações reais e atuais do computador."""
        return self.execute("get_system_info", {})

    def _gemini_list_directory(self, path: str):
        """Lista os arquivos e pastas de um diretório."""
        return self.execute(
            "list_directory",
            {"path": path}
        )

    def _gemini_list_directory_recursive(
        self,
        path: str,
        max_depth: int = 3
    ):
        """Lista recursivamente arquivos e pastas."""
        return self.execute(
            "list_directory_recursive",
            {
                "path": path,
                "max_depth": max_depth
            }
        )

    def _gemini_read_file(
        self,
        path: str,
        max_chars: int = 20000
    ):
        """Lê o conteúdo de um arquivo de texto."""
        return self.execute(
            "read_file",
            {
                "path": path,
                "max_chars": max_chars
            }
        )

    def _gemini_write_file(
        self,
        path: str,
        content: str
    ):
        """Escreve em arquivo após confirmação."""
        return self.execute(
            "write_file",
            {
                "path": path,
                "content": content
            }
        )

    def _function_schema(
        self,
        name,
        description,
        properties,
        required
    ):
        return {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }

    def get_openai_tools(self):
        """Ferramentas no formato OpenAI-compatible."""

        return [
            self._function_schema(
                "get_system_info",
                (
                    "Obtém informações reais e atuais do computador, "
                    "incluindo sistema operacional, kernel, CPU, GPU, "
                    "RAM e armazenamento."
                ),
                {},
                []
            ),
            self._function_schema(
                "list_directory",
                "Lista arquivos e pastas de um diretório.",
                {
                    "path": {
                        "type": "string",
                        "description": "Caminho do diretório."
                    }
                },
                ["path"]
            ),
            self._function_schema(
                "list_directory_recursive",
                (
                    "Lista recursivamente arquivos e pastas de um "
                    "diretório e suas subpastas."
                ),
                {
                    "path": {
                        "type": "string",
                        "description": "Caminho do diretório."
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "Profundidade máxima, de 0 a 3."
                    }
                },
                ["path"]
            ),
            self._function_schema(
                "read_file",
                "Lê o conteúdo de um arquivo de texto.",
                {
                    "path": {
                        "type": "string",
                        "description": "Caminho do arquivo."
                    },
                    "max_chars": {
                        "type": "integer",
                        "description": "Máximo de caracteres."
                    }
                },
                ["path"]
            ),
            self._function_schema(
                "write_file",
                (
                    "Cria ou substitui um arquivo dentro da pasta "
                    "pessoal do usuário. A aplicação exige "
                    "confirmação antes da execução."
                ),
                {
                    "path": {
                        "type": "string",
                        "description": "Caminho do arquivo."
                    },
                    "content": {
                        "type": "string",
                        "description": "Conteúdo completo do arquivo."
                    }
                },
                ["path", "content"]
            ),
        ]

    def get_openrouter_tools(self, web_search=False):
        tools = self.get_openai_tools()

        if web_search:
            tools.append({
                "type": "openrouter:web_search",
                "parameters": {
                    "max_results": 5,
                    "max_total_results": 10
                }
            })

        return tools

    def get_tool_result_json(self, result):
        return json.dumps(
            result,
            ensure_ascii=False
        )
