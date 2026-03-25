"""Tests for the alert summarisation module.

Verifies that summarise_alert correctly calls the Anthropic client
and returns the expected summary string.
"""

import pytest

from models.alert import AlertPayload
from modules.summariser import summarise_alert


@pytest.mark.asyncio
async def test_summarise_alert_returns_string(sample_alert, mock_anthropic_client):
    """summarise_alert should return a non-empty string."""
    result = await summarise_alert(sample_alert)
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_summarise_alert_calls_anthropic(sample_alert, mock_anthropic_client):
    """summarise_alert should call the Anthropic client exactly once."""
    await summarise_alert(sample_alert)
    mock_anthropic_client.assert_called_once()


@pytest.mark.asyncio
async def test_summarise_alert_includes_rule_name(sample_alert, mock_anthropic_client):
    """The user message sent to Claude should include the alert's rule name."""
    await summarise_alert(sample_alert)
    call_args = mock_anthropic_client.call_args
    user_message = call_args.kwargs.get("user_message", call_args.args[1] if len(call_args.args) > 1 else "")
    assert sample_alert.rule_name in user_message


@pytest.mark.asyncio
async def test_summarise_alert_max_tokens_256(sample_alert, mock_anthropic_client):
    """summarise_alert should request at most 256 tokens."""
    await summarise_alert(sample_alert)
    call_args = mock_anthropic_client.call_args
    max_tokens = call_args.kwargs.get("max_tokens", call_args.args[2] if len(call_args.args) > 2 else None)
    assert max_tokens == 256


@pytest.mark.asyncio
async def test_summarise_alert_returns_mock_value(sample_alert, mock_anthropic_client):
    """summarise_alert should return exactly the mocked response."""
    result = await summarise_alert(sample_alert)
    assert result == "Mocked AI response for testing purposes."
