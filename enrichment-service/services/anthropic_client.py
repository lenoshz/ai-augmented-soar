"""Async Anthropic SDK wrapper for the AI-Augmented SOAR enrichment service.

Provides a singleton client with retry logic, token tracking, and
both single-turn and multi-turn conversation methods.
"""

import asyncio
import logging
from typing import Any

import anthropic

from config import settings

logger = logging.getLogger("ai-augmented-soar")

# Retry delays in seconds for rate-limit / overload errors
_RETRY_DELAYS = [2, 4, 8]


class AnthropicClient:
    """Async wrapper around the Anthropic SDK with retry and token tracking."""

    def __init__(self) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.total_input_tokens: int = 0
        self.total_output_tokens: int = 0

    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 1024,
    ) -> str:
        """Send a single-turn request and return the response text.

        Retries on HTTP 429 (rate limit) and 529 (overload) with
        exponential back-off delays of 2, 4, and 8 seconds.
        """
        for attempt, delay in enumerate([0] + _RETRY_DELAYS):
            if delay:
                logger.debug("Anthropic retry attempt %d – sleeping %ds", attempt, delay)
                await asyncio.sleep(delay)
            try:
                response = await self._client.messages.create(
                    model=settings.anthropic_model,
                    max_tokens=max_tokens,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_message}],
                )
                self.total_input_tokens += response.usage.input_tokens
                self.total_output_tokens += response.usage.output_tokens
                logger.debug(
                    "Anthropic complete: in=%d out=%d total_in=%d total_out=%d",
                    response.usage.input_tokens,
                    response.usage.output_tokens,
                    self.total_input_tokens,
                    self.total_output_tokens,
                )
                return response.content[0].text
            except anthropic.APIStatusError as exc:
                if exc.status_code in (429, 529) and attempt < len(_RETRY_DELAYS):
                    logger.warning(
                        "Anthropic API status %d on attempt %d – will retry",
                        exc.status_code,
                        attempt + 1,
                    )
                    continue
                raise

        # Should not reach here, but satisfy type checker
        raise RuntimeError("Anthropic complete exhausted all retries")

    async def complete_with_history(
        self,
        system_prompt: str,
        messages: list[dict[str, Any]],
        max_tokens: int = 1024,
    ) -> str:
        """Send a multi-turn conversation request and return the response text.

        Args:
            system_prompt: System-level instructions for the conversation.
            messages: List of {role, content} dicts representing conversation history.
            max_tokens: Maximum tokens in the response.
        """
        for attempt, delay in enumerate([0] + _RETRY_DELAYS):
            if delay:
                logger.debug("Anthropic retry attempt %d – sleeping %ds", attempt, delay)
                await asyncio.sleep(delay)
            try:
                response = await self._client.messages.create(
                    model=settings.anthropic_model,
                    max_tokens=max_tokens,
                    system=system_prompt,
                    messages=messages,
                )
                self.total_input_tokens += response.usage.input_tokens
                self.total_output_tokens += response.usage.output_tokens
                logger.debug(
                    "Anthropic complete_with_history: in=%d out=%d",
                    response.usage.input_tokens,
                    response.usage.output_tokens,
                )
                return response.content[0].text
            except anthropic.APIStatusError as exc:
                if exc.status_code in (429, 529) and attempt < len(_RETRY_DELAYS):
                    logger.warning(
                        "Anthropic API status %d on attempt %d – will retry",
                        exc.status_code,
                        attempt + 1,
                    )
                    continue
                raise

        raise RuntimeError("Anthropic complete_with_history exhausted all retries")


# Singleton instance
anthropic_client = AnthropicClient()
