from core.tool_manager import ToolManager
from llm.gateway import LLMGateway


class Agent:

    def __init__(self):
        self.tool_manager = ToolManager(
            confirmation_callback=self.confirm_action
        )

        self.llm = LLMGateway(
            tool_manager=self.tool_manager
        )

    def process(self, message, on_event=None, voice_mode=False):
        return self.llm.chat(
            message,
            on_event=on_event,
            voice_mode=voice_mode,
        )

    def confirm_action(self, tool_name, arguments):
        print()
        print("╭──────────────────────────────────╮")
        print("│          CONFIRMAÇÃO NIX          │")
        print("╰──────────────────────────────────╯")

        if tool_name == "write_file":
            path = arguments.get("path", "desconhecido")
            content = arguments.get("content", "")

            print(f"Arquivo: {path}")
            print(f"Caracteres: {len(content)}")
            print()
            print("Conteúdo que será escrito:")
            print("──────────────────────────────────")
            print(content[:1000])

            if len(content) > 1000:
                print("... [conteúdo cortado]")

        else:
            print(f"Ferramenta: {tool_name}")
            print(f"Argumentos: {arguments}")

        print()
        print("[1] Confirmar somente esta vez")
        print("[2] Permitir esta ferramenta nesta sessão")
        print("[3] Cancelar")

        choice = input("\nEscolha: ").strip()

        if choice == "2":
            self.tool_manager.permissions.grant_for_session(
                tool_name
            )
            return True

        return choice == "1"
