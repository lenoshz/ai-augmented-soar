"""Alert summarisation module for the AI-Augmented SOAR enrichment service.

Uses Claude to produce a concise plain-language summary of a security alert
that can be immediately understood by a SOC analyst.
"""

import logging

from models.alert import AlertPayload
from services.anthropic_client import anthropic_client

logger = logging.getLogger("ai-augmented-soar")

SUMMARISER_SYSTEM_PROMPT = (
    "You are a senior SOC analyst. Your task is to write a concise, plain-language summary "
    "of a security alert that can be immediately understood by an analyst who may not have "
    "deep technical context. Focus on: what happened, which asset is affected, why it matters, "
    "and the likely adversary intent. Keep the summary to 2-3 sentences."
)


async def summarise_alert(alert: AlertPayload) -> str:
    """Generate a plain-language summary of the given alert.

    Args:
        alert: The incoming alert payload.

    Returns:
        A 2-3 sentence AI-generated summary string.
    """
    logger.debug("Summarising alert %s", alert.alert_id)

    user_message = (
        f"Rule: {alert.rule_name}\n"
        f"Severity: {alert.severity}\n"
        f"Host: {alert.host_name or 'unknown'}\n"
        f"User: {alert.user_name or 'unknown'}\n"
        f"Process: {alert.process_name or 'N/A'}\n"
        f"Command: {alert.process_command_line or 'N/A'}\n"
        f"Description: {alert.description or 'No description provided'}\n"
        f"Tags: {', '.join(alert.tags) if alert.tags else 'None'}"
    )

    return await anthropic_client.complete(
        system_prompt=SUMMARISER_SYSTEM_PROMPT,
        user_message=user_message,
        max_tokens=256,
    )
