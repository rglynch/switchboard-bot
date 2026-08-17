"""
LLM service — initializes and exposes the provider registry.
Import `registry` from here and use it everywhere.
"""

import logging

from bot.config import (
    LLM_DEFAULT_PROVIDER,
    ANTHROPIC_API_KEY, ANTHROPIC_MODEL,
    OPENAI_API_KEY, OPENAI_MODEL,
    PERPLEXITY_API_KEY, PERPLEXITY_MODEL,
    GROK_API_KEY, GROK_MODEL,
)
from bot.services.llm_providers.base import LLMRegistry
from bot.services.llm_providers.claude import ClaudeProvider
from bot.services.llm_providers.openai import GPTProvider
from bot.services.llm_providers.perplexity import PerplexityProvider
from bot.services.llm_providers.grok import GrokProvider

logger = logging.getLogger(__name__)


def build_registry() -> LLMRegistry:
    reg = LLMRegistry(default=LLM_DEFAULT_PROVIDER)

    if ANTHROPIC_API_KEY:
        reg.register(ClaudeProvider(ANTHROPIC_API_KEY, ANTHROPIC_MODEL))

    if OPENAI_API_KEY:
        reg.register(GPTProvider(OPENAI_API_KEY, OPENAI_MODEL))

    if PERPLEXITY_API_KEY:
        reg.register(PerplexityProvider(PERPLEXITY_API_KEY, PERPLEXITY_MODEL))

    if GROK_API_KEY:
        reg.register(GrokProvider(GROK_API_KEY, GROK_MODEL))

    logger.info("LLM providers available: %s (default: %s)", reg.available, reg.default_name)
    return reg


registry = build_registry()
