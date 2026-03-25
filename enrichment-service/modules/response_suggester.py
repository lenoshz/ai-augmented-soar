"""Response suggestion module for the AI-Augmented SOAR enrichment service.

Generates structured response playbooks and handles multi-turn analyst
chat conversations for alert investigation guidance.
"""

import json
import logging
from typing import Any

from models.alert import AlertPayload
from models.enrichment import AlertContext, ResponseSuggestion
from services.anthropic_client import anthropic_client

logger = logging.getLogger("ai-augmented-soar")

RESPONSE_SYSTEM_PROMPT = (
    "You are a senior incident responder. Given a security alert with MITRE ATT&CK context, "
    "respond ONLY with valid JSON containing exactly these keys:\n"
    "  - immediate_actions: list of strings (containment and triage steps)\n"
    "  - investigation_steps: list of strings (deeper investigation steps)\n"
    "  - escalation_criteria: string (when to escalate)\n"
    "  - eql_hunt_query: string (an EQL query to hunt for related activity)\n"
    "Provide practical, actionable guidance. Do not include any text outside the JSON."
)

CHAT_SYSTEM_PROMPT = (
    "You are an expert SOC analyst assistant helping an analyst investigate a security alert. "
    "You have full context about the alert and any enrichment that has been performed. "
    "Answer questions clearly, suggest investigation steps, and help interpret findings. "
    "Be concise and practical."
)


def _build_alert_context_message(alert: AlertPayload, context: AlertContext) -> str:
    """Format alert and context data into a human-readable message for Claude."""
    return (
        f"Alert: {alert.rule_name} (severity: {alert.severity})\n"
        f"Host: {alert.host_name or 'unknown'} | User: {alert.user_name or 'unknown'}\n"
        f"MITRE Tactic: {context.mitre_tactic} ({context.mitre_tactic_id})\n"
        f"MITRE Technique: {context.mitre_technique} ({context.mitre_technique_id})\n"
        f"Asset Owner: {context.asset_owner or 'unknown'} | "
        f"Criticality: {context.asset_criticality or 'unknown'}\n"
        f"IOC Hits: {', '.join(context.ioc_hits) if context.ioc_hits else 'None'}\n"
        f"Similar alerts (7d): {context.similar_alert_count}"
    )


async def suggest_response(alert: AlertPayload, context: AlertContext) -> ResponseSuggestion:
    """Generate a structured response playbook for the given alert and context.

    Falls back to empty ResponseSuggestion on JSON parse failure.
    """
    logger.debug("Generating response suggestion for alert %s", alert.alert_id)

    user_message = _build_alert_context_message(alert, context)

    try:
        raw = await anthropic_client.complete(
            system_prompt=RESPONSE_SYSTEM_PROMPT,
            user_message=user_message,
            max_tokens=1024,
        )
        parsed: dict[str, Any] = json.loads(raw)
        return ResponseSuggestion(
            immediate_actions=parsed.get("immediate_actions", []),
            investigation_steps=parsed.get("investigation_steps", []),
            escalation_criteria=parsed.get("escalation_criteria", ""),
            eql_hunt_query=parsed.get("eql_hunt_query", ""),
        )
    except (json.JSONDecodeError, Exception) as exc:
        logger.warning(
            "Response suggestion failed for alert %s: %s – using empty fallback",
            alert.alert_id,
            exc,
        )
        return ResponseSuggestion()


async def handle_analyst_chat(
    alert: AlertPayload,
    context: AlertContext,
    history: list[dict[str, Any]],
    user_message: str,
) -> str:
    """Handle a multi-turn analyst chat message about an alert.

    Args:
        alert: The alert being investigated.
        context: Enriched context for the alert.
        history: Previous conversation turns as {role, content} dicts.
        user_message: The analyst's latest message.

    Returns:
        The assistant's response string.
    """
    logger.debug("Handling analyst chat for alert %s", alert.alert_id)

    alert_context_summary = _build_alert_context_message(alert, context)
    system_prompt = f"{CHAT_SYSTEM_PROMPT}\n\nAlert Context:\n{alert_context_summary}"

    messages = list(history)
    messages.append({"role": "user", "content": user_message})

    return await anthropic_client.complete_with_history(
        system_prompt=system_prompt,
        messages=messages,
        max_tokens=1024,
    )
