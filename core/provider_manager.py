import os
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ProviderState:
    status: str = "available"
    reason: str | None = None
    retry_at: float | None = None
    last_model: str | None = None


class ProviderManager:

    AVAILABLE = "available"
    RATE_LIMITED = "rate_limited"
    QUOTA_EXCEEDED = "quota_exceeded"
    AUTH_ERROR = "auth_error"
    TEMPORARILY_UNAVAILABLE = "temporarily_unavailable"
    NOT_CONFIGURED = "not_configured"
    DISABLED = "disabled"

    PROVIDER_KEYS = {
        "openrouter": "OPENROUTER_API_KEY",
        "groq": "GROQ_API_KEY",
        "mistral": "MISTRAL_API_KEY",
        "sambanova": "SAMBANOVA_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "cohere": "COHERE_API_KEY",
        "huggingface": "HF_TOKEN",
        "cloudflare": "CLOUDFLARE_API_TOKEN",
    }

    def __init__(self):
        self.providers = [
            "openrouter",
            "groq",
            "mistral",
            "sambanova",
            "gemini",
            "cohere",
            "huggingface",
            "cloudflare",
        ]

        self.states = {}

        for provider in self.providers:
            key_name = self.PROVIDER_KEYS.get(provider)

            if key_name and os.getenv(key_name):
                self.states[provider] = ProviderState(
                    status=self.AVAILABLE
                )
            else:
                self.states[provider] = ProviderState(
                    status=self.NOT_CONFIGURED,
                    reason=(
                        f"{key_name} não configurada."
                        if key_name
                        else "Credencial não configurada."
                    )
                )

    def is_available(self, provider):
        """Verifica se o provedor pode ser utilizado."""

        state = self.states.get(provider)

        if state is None:
            return False

        if state.status == self.AVAILABLE:
            return True

        if (
            state.status == self.RATE_LIMITED
            and state.retry_at is not None
        ):
            if datetime.now().timestamp() >= state.retry_at:
                self.enable(provider)
                return True

        return False

    def get_available_providers(self):
        """Retorna os provedores disponíveis na ordem definida."""

        return [
            provider
            for provider in self.providers
            if self.is_available(provider)
        ]

    def disable(
        self,
        provider,
        status,
        reason=None,
        retry_at=None,
    ):
        """Atualiza o estado de um provedor."""

        if provider not in self.states:
            return

        current_model = self.states[provider].last_model

        self.states[provider] = ProviderState(
            status=status,
            reason=reason,
            retry_at=retry_at,
            last_model=current_model,
        )

    def enable(self, provider):
        """Reativa um provedor."""

        if provider not in self.states:
            return

        current_model = self.states[provider].last_model

        self.states[provider] = ProviderState(
            status=self.AVAILABLE,
            last_model=current_model,
        )

    def set_model(self, provider, model):
        """Registra o último modelo utilizado."""

        if provider not in self.states:
            return

        self.states[provider].last_model = model

    def get_state(self, provider):
        """Retorna o estado de um provedor."""

        return self.states.get(provider)

    def get_status(self):
        """Retorna o estado de todos os provedores."""

        result = {}

        for provider in self.providers:
            state = self.states[provider]

            result[provider] = {
                "status": state.status,
                "motivo": state.reason,
                "retry_at": state.retry_at,
                "modelo": state.last_model,
            }

        return result