import sys

from config.env import load_environment
from core.agent import Agent


def print_header():
    print("╭──────────────────────────────╮")
    print("│            N I X             │")
    print("│       Sistema iniciado       │")
    print("╰──────────────────────────────╯")


def print_response(agent, response):
    model_info = agent.llm.get_last_model()

    print()

    if model_info:
        print(
            f"Nix "
            f"[{model_info['provider']} • "
            f"{model_info['model']}]"
        )
    else:
        print("Nix")

    print(response)


def print_providers(agent):
    statuses = agent.llm.get_provider_status()

    print("\nProvedores:")
    print("────────────────────────────────────────────")

    for provider, state in statuses.items():
        print(
            f"{provider:<13}"
            f"{state['status']:<24}"
            f"{state['modelo'] or '-'}"
        )


def text_mode():
    agent = Agent()

    print_header()

    while True:
        try:
            message = input("\nVocê: ").strip()

            if message.lower() in [
                "sair",
                "exit",
                "quit",
            ]:
                print("\nAté mais.")
                break

            if message.lower() == "/provedores":
                print_providers(agent)
                continue

            if not message:
                continue

            response = agent.process(message)

            print_response(
                agent,
                response,
            )

        except KeyboardInterrupt:
            print("\nAté mais.")
            break


def voice_mode():
    from voice.assistant import VoiceAssistant

    agent = Agent()

    assistant = VoiceAssistant(
        agent=agent
    )

    assistant.run()


def main():
    load_environment()

    if "--voice" in sys.argv:
        voice_mode()
    else:
        text_mode()


if __name__ == "__main__":
    main()