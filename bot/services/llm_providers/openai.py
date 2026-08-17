"""OpenAI GPT provider."""

import httpx
from bot.services.llm_providers.base import LLMProvider

DEFAULT_SYSTEM = (
    "You are a helpful assistant in a Telegram group chat. "
    "Keep responses concise and conversational. Max 2-3 paragraphs."
)


class GPTProvider(LLMProvider):
    name = "gpt"

    model_aliases = {
        "5.4":      "gpt-5.4",
        "5.4-mini": "gpt-5.4-mini",
        "mini":     "gpt-5.4-mini",
        "5.4-nano": "gpt-5.4-nano",
        "nano":     "gpt-5.4-nano",
        "4.1":      "gpt-4.1",
        "4.1-mini": "gpt-4.1-mini",
    }

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.default_model = model

    async def chat(self, message: str, system_prompt: str | None = None, model_override: str | None = None, web_search: bool = False) -> str:
        model = model_override or self.default_model
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": model,
            "max_completion_tokens": 1024,
            "messages": [
                {"role": "system", "content": system_prompt or DEFAULT_SYSTEM},
                {"role": "user", "content": message},
            ],
        }

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()