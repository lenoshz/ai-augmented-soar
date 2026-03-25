"""Tests for the context enrichment module.

Covers the success path, JSON decode fallback, and count exception fallback.
"""

import json
from unittest.mock import AsyncMock, patch

import pytest

from models.alert import AlertPayload
from models.enrichment import AlertContext
from modules.context_enricher import enrich_alert, get_similar_alert_count


@pytest.mark.asyncio
async def test_enrich_alert_success_path(sample_alert, mock_elastic_client):
    """enrich_alert should return an AlertContext on the happy path."""
    mitre_json = json.dumps(
        {
            "tactic_name": "Execution",
            "tactic_id": "TA0002",
            "technique_name": "PowerShell",
            "technique_id": "T1059.001",
        }
    )

    with patch(
        "services.anthropic_client.anthropic_client.complete",
        new_callable=AsyncMock,
        return_value=mitre_json,
    ):
        result = await enrich_alert(sample_alert)

    assert isinstance(result, AlertContext)
    assert result.mitre_tactic == "Execution"
    assert result.mitre_tactic_id == "TA0002"
    assert result.mitre_technique == "PowerShell"
    assert result.mitre_technique_id == "T1059.001"


@pytest.mark.asyncio
async def test_enrich_alert_json_decode_fallback(sample_alert, mock_elastic_client):
    """enrich_alert should fall back to Unknown values when Claude returns invalid JSON."""
    with patch(
        "services.anthropic_client.anthropic_client.complete",
        new_callable=AsyncMock,
        return_value="This is not JSON at all.",
    ):
        result = await enrich_alert(sample_alert)

    assert isinstance(result, AlertContext)
    assert result.mitre_tactic == "Unknown"
    assert result.mitre_tactic_id == "Unknown"
    assert result.mitre_technique == "Unknown"
    assert result.mitre_technique_id == "Unknown"


@pytest.mark.asyncio
async def test_enrich_alert_count_exception_fallback(sample_alert):
    """enrich_alert should return similar_alert_count=0 when ES count fails."""
    mitre_json = json.dumps(
        {
            "tactic_name": "Execution",
            "tactic_id": "TA0002",
            "technique_name": "PowerShell",
            "technique_id": "T1059.001",
        }
    )

    with (
        patch(
            "services.anthropic_client.anthropic_client.complete",
            new_callable=AsyncMock,
            return_value=mitre_json,
        ),
        patch(
            "services.elastic_client.elastic_client.count",
            new_callable=AsyncMock,
            side_effect=Exception("Elasticsearch unavailable"),
        ),
    ):
        result = await enrich_alert(sample_alert)

    assert result.similar_alert_count == 0


@pytest.mark.asyncio
async def test_get_similar_alert_count_returns_zero_on_error():
    """get_similar_alert_count should return 0 when Elasticsearch raises an exception."""
    with patch(
        "services.elastic_client.elastic_client.count",
        new_callable=AsyncMock,
        side_effect=Exception("Connection refused"),
    ):
        count = await get_similar_alert_count("Test Rule")

    assert count == 0


@pytest.mark.asyncio
async def test_get_similar_alert_count_returns_count(mock_elastic_client):
    """get_similar_alert_count should return the value from Elasticsearch."""
    mock_elastic_client["count"].return_value = 5
    count = await get_similar_alert_count("Suspicious PowerShell Execution")
    assert count == 5
