import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent

ENV_FILE = PROJECT_ROOT / ".env"


def load_environment():
    """Carrega as variáveis do arquivo .env."""

    load_dotenv(ENV_FILE)


def get_env(name: str, default=None):
    """Retorna uma variável de ambiente."""

    return os.getenv(
        name,
        default
    )


def is_configured(name: str):
    """Verifica se uma variável está configurada."""

    value = os.getenv(name)

    return bool(
        value and value.strip()
    )