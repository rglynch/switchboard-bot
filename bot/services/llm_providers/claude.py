"""Anthropic Claude provider."""

import httpx
from bot.services.llm_providers.base import LLMProvider

DEFAULT_SYSTEM = (
    "You are a helpful assistant in a Telegram group chat. "
    "Keep responses concise and conversational. Max 2-3 paragraphs."
)


class ClaudeProvider(LLMProvider):
    name = "claude"

    # Model shortcuts. Each ID is one model version; pointing a shortcut at a newer model means editing it here.
    model_aliases = {
        "haiku":   "claude-haiku-4-5",
        "sonnet":  "claude-sonnet-4-6",
        "opus":    "claude-opus-4-6",
    }

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.default_model = model

    async def chat(self, message: str, system_prompt: str | None = None, model_override: str | None = None, web_search: bool = False) -> str:
        model = model_override or self.default_model
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": model,
            "max_tokens": 1024,
            "system": system_prompt or DEFAULT_SYSTEM,
            "messages": [{"role": "user", "content": message}],
        }

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
            resp.raise_for_status()
        return resp.json()["content"][0]["text"].strip()