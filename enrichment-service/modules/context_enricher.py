"""Context enrichment module for the AI-Augmented SOAR enrichment service.

Classifies alerts with MITRE ATT&CK tactics and techniques, looks up asset
ownership, queries threat intel for IOCs, and counts similar recent alerts.
"""

import json
import logging
from typing import Any

from models.alert import AlertPayload
from models.enrichment import AlertContext
from services.anthropic_client import anthropic_client
from services.elastic_client import elastic_client
from services.mitre_client import mitre_client
from services.threat_intel_client import threat_intel_client

logger = logging.getLogger("ai-augmented-soar")

MITRE_SYSTEM_PROMPT = (
    "You are a MITRE ATT&CK expert. Given a security alert, respond ONLY with valid JSON "
    "containing exactly these keys: tactic_name, tactic_id, technique_name, technique_id. "
    "If you cannot determine the classification, use the string \"Unknown\" for each value. "
    "Do not include any explanation or text outside the JSON object."
)

# Asset inventory mapping hostname patterns to owner/criticality metadata
ASSET_INVENTORY: dict[str, dict[str, str]] = {
    "dc": {"owner": "IT Infrastructure", "criticality": "critical"},
    "exchange": {"owner": "IT Infrastructure", "criticality": "critical"},
    "fin": {"owner": "Finance", "criticality": "high"},
    "hr": {"owner": "Human Resources", "criticality": "high"},
    "dev": {"owner": "Engineering", "criticality": "medium"},
    "web": {"owner": "Engineering", "criticality": "high"},
    "db": {"owner": "Data Engineering", "criticality": "critical"},
    "vpn": {"owner": "IT Infrastructure", "criticality": "high"},
    "backup": {"owner": "IT Infrastructure", "criticality": "critical"},
    "workstation": {"owner": "End User Computing", "criticality": "low"},
}


async def get_similar_alert_count(rule_name: str) -> int:
    """Count similar alerts fired by the same rule in the last 7 days.

    Returns 0 on any error to avoid blocking the enrichment pipeline.
    """
    try:
        return await elastic_client.count(
            index="ai-augmented-soar-enriched",
            query={
                "bool": {
                    "must": [
                        {"term": {"rule_name.keyword": rule_name}},
                        {"range": {"enriched_at": {"gte": "now-7d"}}},
                    ]
                }
            },
        )
    except Exception as exc:
        logger.warning("Failed to count similar alerts for rule '%s': %s", rule_name, exc)
        return 0


def _lookup_asset(host_name: str | None) -> dict[str, str | None]:
    """Look up asset metadata from the inventory based on hostname pattern."""
    if not host_name:
        return {"owner": None, "criticality": None}
    host_lower = host_name.lower()
    for pattern, info in ASSET_INVENTORY.items():
        if pattern in host_lower:
            return {"owner": info["owner"], "criticality": info["criticality"]}
    return {"owner": None, "criticality": None}


async def enrich_alert(alert: AlertPayload) -> AlertContext:
    """Run the full context enrichment pipeline for an alert.

    Steps:
    1. Classify alert with MITRE ATT&CK via Claude
    2. Look up asset owner/criticality from internal inventory
    3. Query threat intel for IOCs (if feature flags enabled)
    4. Count similar alerts from the last 7 days

    Returns an AlertContext with safe defaults on any partial failure.
    """
    logger.debug("Enriching context for alert %s", alert.alert_id)

    # Step 1: MITRE classification via Claude
    mitre_data: dict[str, Any] = {
        "tactic_name": "Unknown",
        "tactic_id": "Unknown",
        "technique_name": "Unknown",
        "technique_id": "Unknown",
    }

    user_message = (
        f"Rule: {alert.rule_name}\n"
        f"Description: {alert.description or 'N/A'}\n"
        f"Tags: {', '.join(alert.tags) if alert.tags else 'None'}\n"
        f"Process: {alert.process_name or 'N/A'}\n"
        f"Command: {alert.process_command_line or 'N/A'}"
    )

    try:
        raw = await anthropic_client.complete(
            system_prompt=MITRE_SYSTEM_PROMPT,
            user_message=user_message,
            max_tokens=128,
        )
        parsed = json.loads(raw)
        mitre_data.update(parsed)
        logger.debug("MITRE classification for %s: %s", alert.alert_id, mitre_data)
    except (json.JSONDecodeError, Exception) as exc:
        logger.warning(
            "MITRE classification failed for alert %s: %s – using unknown fallback",
            alert.alert_id,
            exc,
        )

    # Step 2: Asset inventory lookup
    asset = _lookup_asset(alert.host_name)

    # Step 3: Threat intel IOC lookup
    ioc_hits: list[str] = []
    if alert.network_destination_ip:
        ioc_hits.extend(await threat_intel_client.lookup_ip(alert.network_destination_ip))
    if alert.host_ip:
        ioc_hits.extend(await threat_intel_client.lookup_ip(alert.host_ip))

    # Step 4: Count similar alerts
    similar_count = await get_similar_alert_count(alert.rule_name)

    return AlertContext(
        mitre_tactic=mitre_data.get("tactic_name", "Unknown"),
        mitre_tactic_id=mitre_data.get("tactic_id", "Unknown"),
        mitre_technique=mitre_data.get("technique_name", "Unknown"),
        mitre_technique_id=mitre_data.get("technique_id", "Unknown"),
        asset_owner=asset["owner"],
        asset_criticality=asset["criticality"],
        ioc_hits=ioc_hits,
        similar_alert_count=similar_count,
    )
