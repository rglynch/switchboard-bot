"""xAI Grok provider with optional web search.

Normal queries use /v1/chat/completions (fast, cheap).
Web search queries use /v1/responses (required for server-side tools).
"""

import logging

import httpx
from bot.services.llm_providers.base import LLMProvider

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM = (
    "You are a helpful assistant in a Telegram group chat. "
    "Keep responses concise and conversational. Max 2-3 paragraphs."
)

CHAT_URL = "https://api.x.ai/v1/chat/completions"
RESPONSES_URL = "https://api.x.ai/v1/responses"


class GrokProvider(LLMProvider):
    name = "grok"

    model_aliases = {
        "fast":           "grok-4-1-fast",
        "fast-noreason":  "grok-4-1-fast-non-reasoning",
        "4":              "grok-4",
        "3":              "grok-3",
    }

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.default_model = model

    async def chat(
        self,
        message: str,
        system_prompt: str | None = None,
        model_override: str | None = None,
        web_search: bool = False,
    ) -> str:
        model = model_override or self.default_model
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        if web_search:
            return await self._responses_api(message, model, headers, system_prompt)
        else:
            return await self._chat_api(message, model, headers, system_prompt)

    async def _chat_api(self, message: str, model: str, headers: dict, system_prompt: str | None) -> str:
        """Standard chat completions — fast, no tools."""
        payload = {
            "model": model,
            "max_tokens": 1024,
            "temperature": 0.7,
            "messages": [
                {"role": "system", "content": system_prompt or DEFAULT_SYSTEM},
                {"role": "user", "content": message},
            ],
        }

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(CHAT_URL, headers=headers, json=payload)
            resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()

    async def _responses_api(self, message: str, model: str, headers: dict, system_prompt: str | None) -> str:
        """Responses API — required for server-side tools like web search."""
        instructions = system_prompt or DEFAULT_SYSTEM
        payload = {
            "model": model,
            "instructions": instructions,
            "input": [
                {"role": "user", "content": message},
            ],
            "tools": [{"type": "web_search"}],
        }

        async with httpx.AsyncClient(timeout=90) as client:
            resp = await client.post(RESPONSES_URL, headers=headers, json=payload)
            resp.raise_for_status()

        data = resp.json()

        # Responses API returns output as a list of items
        # Find the message item with the assistant's text
        for item in data.get("output", []):
            if item.get("type") == "message" and item.get("role") == "assistant":
                # Content is a list of content blocks
                for block in item.get("content", []):
                    if block.get("type") == "output_text":
                        return block["text"].strip()

        # Fallback: try to find any text content in the output
        for item in data.get("output", []):
            if isinstance(item, dict):
                content = item.get("content")
                if isinstance(content, str):
                    return content.strip()
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and "text" in block:
                            return block["text"].strip()

        logger.warning("Grok Responses API: could not extract text from response: %s", data)
        return "Got a response but couldn't parse it. Try again without :web."