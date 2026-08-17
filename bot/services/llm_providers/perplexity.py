"""Perplexity Sonar provider — search-grounded AI answers."""

import httpx
from bot.services.llm_providers.base import LLMProvider

DEFAULT_SYSTEM = (
    "You are a helpful research assistant in a Telegram group chat. "
    "Provide concise, well-sourced answers. Include relevant URLs when available."
)


class PerplexityProvider(LLMProvider):
    name = "perplexity"

    model_aliases = {
        "sonar":     "sonar",
        "pro":       "sonar-pro",
        "reasoning": "sonar-reasoning-pro",
    }

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.default_model = model

    async def chat(self, message: str, system_prompt: str | None = None, model_override: str | None = None, web_search: bool = False) -> str:
        model = model_override or self.default_model
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt or DEFAULT_SYSTEM},
                {"role": "user", "content": message},
            ],
        }

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post("https://api.perplexity.ai/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        text = data["choices"][0]["message"]["content"].strip()

        citations = data.get("citations", [])
        if citations:
            cite_lines = "\n".join(f"[{i+1}] {url}" for i, url in enumerate(citations[:5]))
            text += f"\n\n📎 Sources:\n{cite_lines}"

        return text