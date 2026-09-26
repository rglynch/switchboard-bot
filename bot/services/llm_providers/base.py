"""
LLM provider base class and registry.
Supports multiple providers, per-request model overrides,
and per-provider model restrictions via ALLOWED_MODELS_* env vars.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from bot.config import get_allowed_models

logger = logging.getLogger(__name__)


class ModelNotAllowedError(Exception):
    """Raised when a user requests a model that's not in the allowed list."""
    pass


class LLMProvider(ABC):
    """Base class all LLM providers implement."""

    name: str
    default_model: str
    model_aliases: dict[str, str]  # shorthand → full model string

    @abstractmethod
    async def chat(self, message: str, system_prompt: str | None = None, model_override: str | None = None, web_search: bool = False) -> str:
        ...

    def resolve_model(self, shorthand: str | None) -> str:
        """Resolve a shorthand alias to a full model string, checking restrictions."""
        allowed = get_allowed_models(self.name)

        if not shorthand:
            # Using the default model, which is always permitted
            return self.default_model

        key = shorthand.lower()

        # Check restriction BEFORE resolving
        if allowed is not None:
            # Check if the shorthand itself, OR the full resolved string, is in the allowed list
            resolved = self.model_aliases.get(key, key)
            if key not in allowed and resolved.lower() not in allowed:
                permitted = ", ".join(sorted(allowed))
                raise ModelNotAllowedError(
                    f"Model `{shorthand}` is not available for {self.name}.\n"
                    f"Allowed: {permitted}"
                )

        # Resolve: check aliases first, then treat as literal model string
        return self.model_aliases.get(key, shorthand)

    def allowed_models_list(self) -> list[str]:
        """Return the list of models users are allowed to use."""
        allowed = get_allowed_models(self.name)
        if allowed is None:
            return list(self.model_aliases.keys())
        # Return only shortcuts that are in the allowed set,
        # plus any raw model strings in the allowed set
        result = []
        for shortcut in self.model_aliases:
            if shortcut.lower() in allowed:
                result.append(shortcut)
        # Also include raw model strings that aren't shortcuts
        for m in allowed:
            if m not in self.model_aliases and m not in result:
                result.append(m)
        return sorted(result)

    def __repr__(self) -> str:
        return f"<LLMProvider:{self.name} model={self.default_model}>"


class LLMRegistry:
    """Central registry of available LLM providers."""

    def __init__(self, default: str = "grok"):
        self._providers: dict[str, LLMProvider] = {}
        self._default = default

    def register(self, provider: LLMProvider) -> None:
        self._providers[provider.name] = provider
        logger.info("Registered LLM provider: %s (model: %s)", provider.name, provider.default_model)

    @property
    def available(self) -> list[str]:
        return list(self._providers.keys())

    @property
    def default_name(self) -> str:
        return self._default

    def get(self, name: str | None = None) -> LLMProvider:
        key = name or self._default
        if key not in self._providers:
            avail = ", ".join(self.available) or "none"
            raise RuntimeError(
                f"Provider `{key}` not available.\n"
                f"Configured: {avail}"
            )
        return self._providers[key]

    def help_text(self) -> str:
        """Build help string showing providers and their ALLOWED models."""
        lines = []
        for p in self._providers.values():
            default_tag = " ⭐" if p.name == self._default else ""
            models = p.allowed_models_list()
            model_str = ", ".join(models) if models else "(default only)"
            lines.append(f"  {p.name}{default_tag}: {model_str}")
        return "\n".join(lines) if lines else "  No providers configured"

    async def chat(
        self,
        message: str,
        provider: str | None = None,
        model: str | None = None,
        system_prompt: str | None = None,
        web_search: bool = False,
    ) -> tuple[str, str, str]:
        """
        Chat with an LLM provider.
        Returns (response_text, provider_name, model_used).
        Raises ModelNotAllowedError if the requested model is restricted.
        """
        p = self.get(provider)
        resolved_model = p.resolve_model(model)
        response = await p.chat(message, system_prompt=system_prompt, model_override=resolved_model, web_search=web_search)
        return response, p.name, resolved_model