import json
import os
import time

import requests

from google import genai
from google.genai import types

from config.personality import SYSTEM_PROMPT
from core.provider_manager import ProviderManager


class LLMGateway:

    def __init__(self, tool_manager):
        self.messages = []

        self.tool_manager = tool_manager

        self.provider_manager = ProviderManager()

        self.gemini_client = None

        if os.getenv("GEMINI_API_KEY"):
            self.gemini_client = genai.Client()

    def chat(self, message):
        self.messages.append({
            "role": "user",
            "content": message,
        })

        providers = (
            self.provider_manager
            .get_available_providers()
        )

        if not providers:
            return (
                "Não há nenhum provedor de IA "
                "disponível no momento."
            )

        for provider in providers:

            try:
                if provider == "openrouter":
                    answer = self._openrouter()

                elif provider == "groq":
                    answer = self._groq()

                elif provider == "mistral":
                    answer = self._mistral()

                elif provider == "sambanova":
                    answer = self._sambanova()

                elif provider == "gemini":
                    answer = self._gemini()

                elif provider == "cohere":
                    answer = self._cohere()

                elif provider == "huggingface":
                    answer = self._huggingface()

                elif provider == "cloudflare":
                    answer = self._cloudflare()

                else:
                    continue

                self.messages.append({
                    "role": "assistant",
                    "content": answer,
                })

                return answer

            except Exception as error:
                print(
                    f"[LLM] {provider} falhou: {error}"
                )

        return (
            "Todos os provedores disponíveis "
            "falharam nesta sessão."
        )

    def _openrouter(self):
        api_key = os.getenv("OPENROUTER_API_KEY")

        if not api_key:
            self.provider_manager.disable(
                "openrouter",
                ProviderManager.NOT_CONFIGURED,
                "OPENROUTER_API_KEY não configurada.",
            )

            raise RuntimeError(
                "OPENROUTER_API_KEY não configurada"
            )

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            *self.messages,
        ]

        tools = (
            self.tool_manager
            .get_openrouter_tools()
        )

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": (
                    f"Bearer {api_key}"
                ),
                "Content-Type": (
                    "application/json"
                ),
            },
            json={
                "model": os.getenv(
                    "OPENROUTER_MODEL",
                    "openrouter/free",
                ),
                "messages": messages,
                "tools": tools,
                "tool_choice": "auto",
                "plugins": [
                    {
                        "id": "web",
                        "max_results": 5,
                    }
                ],
            },
            timeout=60,
        )

        if response.status_code == 401:
            self.provider_manager.disable(
                "openrouter",
                ProviderManager.AUTH_ERROR,
                "API key inválida ou não autorizada.",
            )

            raise RuntimeError(
                "OpenRouter: API key inválida."
            )

        if response.status_code == 429:
            retry_after = response.headers.get(
                "Retry-After"
            )

            retry_seconds = None

            if retry_after:
                try:
                    retry_seconds = float(retry_after)
                except ValueError:
                    pass

            error_data = {}

            try:
                error_data = response.json()
            except ValueError:
                pass

            error_text = json.dumps(
                error_data,
                ensure_ascii=False,
            ).lower()

            is_daily_quota = (
                "free-models-per-day" in error_text
                or "daily" in error_text
                and "limit" in error_text
            )

            if is_daily_quota:
                self.provider_manager.disable(
                    "openrouter",
                    ProviderManager.QUOTA_EXCEEDED,
                    "Cota diária de modelos gratuitos excedida.",
                )
            else:
                retry_at = None

                if retry_seconds is not None:
                    retry_at = (
                        time.time()
                        + retry_seconds
                    )

                self.provider_manager.disable(
                    "openrouter",
                    ProviderManager.RATE_LIMITED,
                    "Limite temporário de requisições.",
                    retry_at=retry_at,
                )

            raise RuntimeError(
                "OpenRouter atingiu um limite."
            )

        response.raise_for_status()

        data = response.json()

        model = data.get("model")

        if model:
            self.provider_manager.set_model(
                "openrouter",
                model,
            )

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            *self.messages,
        ]

        return self._process_openrouter_response(
            data,
            messages,
        )

    def _process_openrouter_response(
        self,
        data,
        messages,
    ):
        assistant_message = (
            data["choices"][0]["message"]
        )

        tool_calls = assistant_message.get(
            "tool_calls"
        )

        if not tool_calls:
            return assistant_message.get(
                "content",
                "",
            )

        messages.append(
            assistant_message
        )

        for tool_call in tool_calls:

            function_name = (
                tool_call["function"]["name"]
            )

            arguments = (
                tool_call["function"].get(
                    "arguments",
                    "{}",
                )
            )

            try:
                arguments = json.loads(
                    arguments
                )
            except json.JSONDecodeError:
                arguments = {}

            result = self.tool_manager.execute(
                function_name,
                arguments,
            )

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": json.dumps(
                    result,
                    ensure_ascii=False,
                ),
            })

        while True:

            api_key = os.getenv(
                "OPENROUTER_API_KEY"
            )

            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": (
                        f"Bearer {api_key}"
                    ),
                    "Content-Type": (
                        "application/json"
                    ),
                },
                json={
                    "model": os.getenv(
                        "OPENROUTER_MODEL",
                        "openrouter/free",
                    ),
                    "messages": messages,
                    "tools": (
                        self.tool_manager
                        .get_openrouter_tools()
                    ),
                    "tool_choice": "auto",
                },
                timeout=60,
            )

            response.raise_for_status()

            data = response.json()

            model = data.get("model")

            if model:
                self.provider_manager.set_model(
                    "openrouter",
                    model,
                )

            assistant_message = (
                data["choices"][0]["message"]
            )

            more_tool_calls = (
                assistant_message.get(
                    "tool_calls"
                )
            )

            if not more_tool_calls:
                return assistant_message.get(
                    "content",
                    "",
                )

            messages.append(
                assistant_message
            )

            for tool_call in more_tool_calls:

                function_name = (
                    tool_call["function"]["name"]
                )

                arguments = (
                    tool_call["function"].get(
                        "arguments",
                        "{}",
                    )
                )

                try:
                    arguments = json.loads(
                        arguments
                    )
                except json.JSONDecodeError:
                    arguments = {}

                result = self.tool_manager.execute(
                    function_name,
                    arguments,
                )

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(
                        result,
                        ensure_ascii=False,
                    ),
                })

    def _gemini(self):
        if self.gemini_client is None:
            self.provider_manager.disable(
                "gemini",
                ProviderManager.NOT_CONFIGURED,
                "GEMINI_API_KEY não configurada.",
            )

            raise RuntimeError(
                "GEMINI_API_KEY não configurada"
            )

        history = []

        for message in self.messages:
            role = (
                "model"
                if message["role"] == "assistant"
                else "user"
            )

            history.append(
                types.Content(
                    role=role,
                    parts=[
                        types.Part(
                            text=message["content"]
                        )
                    ],
                )
            )

        try:
            response = (
                self.gemini_client
                .models
                .generate_content(
                    model=os.getenv(
                        "GEMINI_MODEL",
                        "gemini-3.6-flash",
                    ),
                    contents=history,
                    config=(
                        types.GenerateContentConfig(
                            system_instruction=(
                                SYSTEM_PROMPT
                            ),
                            tools=(
                                self.tool_manager
                                .get_gemini_tools()
                            ),
                        )
                    ),
                )
            )

            self.provider_manager.set_model(
                "gemini",
                os.getenv(
                    "GEMINI_MODEL",
                    "gemini-3.6-flash",
                ),
            )

            return response.text

        except Exception as error:
            text = str(error).lower()

            if (
                "quota_exceeded" in text
                or (
                    "429" in text
                    and "quota" in text
                    and "daily" in text
                )
            ):
                self.provider_manager.disable(
                    "gemini",
                    ProviderManager.QUOTA_EXCEEDED,
                    "Cota diária do Gemini excedida.",
                )

            elif (
                "rate_limit_exceeded" in text
                or "too_many_requests" in text
            ):
                self.provider_manager.disable(
                    "gemini",
                    ProviderManager.RATE_LIMITED,
                    "Limite temporário de requisições.",
                )

            raise

    def _groq(self):
        return self._openai_compatible_provider(
            provider="groq",
            base_url="https://api.groq.com/openai/v1/chat/completions",
            api_key_name="GROQ_API_KEY",
            model_env="GROQ_MODEL",
        )

    def _mistral(self):
        return self._openai_compatible_provider(
            provider="mistral",
            base_url="https://api.mistral.ai/v1/chat/completions",
            api_key_name="MISTRAL_API_KEY",
            model_env="MISTRAL_MODEL",
        )

    def _sambanova(self):
        return self._openai_compatible_provider(
            provider="sambanova",
            base_url="https://api.sambanova.ai/v1/chat/completions",
            api_key_name="SAMBANOVA_API_KEY",
            model_env="SAMBANOVA_MODEL",
        )

    def _openai_compatible_provider(
        self,
        provider,
        base_url,
        api_key_name,
        model_env,
    ):
        api_key = os.getenv(api_key_name)

        if not api_key:
            self.provider_manager.disable(
                provider,
                ProviderManager.NOT_CONFIGURED,
                f"{api_key_name} não configurada.",
            )

            raise RuntimeError(
                f"{api_key_name} não configurada"
            )

        model = os.getenv(
            model_env,
            "",
        )

        response = requests.post(
            base_url,
            headers={
                "Authorization": (
                    f"Bearer {api_key}"
                ),
                "Content-Type": (
                    "application/json"
                ),
            },
            json={
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT,
                    },
                    *self.messages,
                ],
            },
            timeout=60,
        )

        if response.status_code == 401:
            self.provider_manager.disable(
                provider,
                ProviderManager.AUTH_ERROR,
                "API key inválida.",
            )

            raise RuntimeError(
                f"{provider}: API key inválida."
            )

        if response.status_code == 429:
            self.provider_manager.disable(
                provider,
                ProviderManager.RATE_LIMITED,
                "Limite de requisições atingido.",
            )

            raise RuntimeError(
                f"{provider}: limite atingido."
            )

        response.raise_for_status()

        data = response.json()

        actual_model = data.get(
            "model",
            model,
        )

        self.provider_manager.set_model(
            provider,
            actual_model,
        )

        return data["choices"][0]["message"]["content"]

    def _cohere(self):
        return self._openai_compatible_provider(
            provider="cohere",
            base_url="https://api.cohere.com/v2/chat",
            api_key_name="COHERE_API_KEY",
            model_env="COHERE_MODEL",
        )

    def _huggingface(self):
        return self._openai_compatible_provider(
            provider="huggingface",
            base_url=(
                "https://router.huggingface.co/"
                "v1/chat/completions"
            ),
            api_key_name="HF_TOKEN",
            model_env="HF_MODEL",
        )

    def _cloudflare(self):
        api_token = os.getenv(
            "CLOUDFLARE_API_TOKEN"
        )

        account_id = os.getenv(
            "CLOUDFLARE_ACCOUNT_ID"
        )

        if not api_token or not account_id:
            self.provider_manager.disable(
                "cloudflare",
                ProviderManager.NOT_CONFIGURED,
                "Credenciais Cloudflare ausentes.",
            )

            raise RuntimeError(
                "Cloudflare não configurado."
            )

        model = os.getenv(
            "CLOUDFLARE_MODEL",
            "@cf/openai/gpt-oss-20b",
        )

        url = (
            "https://api.cloudflare.com/client/v4/"
            f"accounts/{account_id}/ai/run/{model}"
        )

        response = requests.post(
            url,
            headers={
                "Authorization": (
                    f"Bearer {api_token}"
                ),
                "Content-Type": (
                    "application/json"
                ),
            },
            json={
                "messages": [
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT,
                    },
                    *self.messages,
                ]
            },
            timeout=60,
        )

        if response.status_code == 401:
            self.provider_manager.disable(
                "cloudflare",
                ProviderManager.AUTH_ERROR,
                "Token Cloudflare inválido.",
            )

            raise RuntimeError(
                "Cloudflare: token inválido."
            )

        response.raise_for_status()

        data = response.json()

        result = data.get(
            "result",
            {},
        )

        response_text = result.get(
            "response"
        )

        if not response_text:
            raise RuntimeError(
                "Cloudflare não retornou uma resposta de texto."
            )

        self.provider_manager.set_model(
            "cloudflare",
            model,
        )

        return response_text

    def get_provider_status(self):
        return (
            self.provider_manager
            .get_status()
        )

    def get_last_model(self):
        for provider in (
            self.provider_manager.providers
        ):
            state = (
                self.provider_manager
                .get_state(provider)
            )

            if state and state.last_model:
                if state.status == (
                    ProviderManager.AVAILABLE
                ):
                    return {
                        "provider": provider,
                        "model": state.last_model,
                    }

        return None