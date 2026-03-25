"""Pytest fixtures for the AI-Augmented SOAR enrichment service tests."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from models.alert import AlertPayload


@pytest.fixture
def sample_alert() -> AlertPayload:
    """Return the first sample alert from the fixtures file."""
    fixtures_path = Path(__file__).parent / "fixtures" / "sample_alerts.json"
    alerts = json.loads(fixtures_path.read_text())
    return AlertPayload(**alerts[0])


@pytest.fixture
def mock_anthropic_client():
    """Patch anthropic_client.complete to return a predefined response."""
    with patch(
        "services.anthropic_client.anthropic_client.complete",
        new_callable=AsyncMock,
        return_value="Mocked AI response for testing purposes.",
    ) as mock:
        yield mock


@pytest.fixture
def mock_elastic_client():
    """Patch elastic_client count and write methods to avoid real ES calls."""
    with (
        patch(
            "services.elastic_client.elastic_client.count",
            new_callable=AsyncMock,
            return_value=3,
        ) as mock_count,
        patch(
            "services.elastic_client.elastic_client.write_enriched_alert",
            new_callable=AsyncMock,
            return_value=None,
        ) as mock_write,
    ):
        yield {"count": mock_count, "write": mock_write}
