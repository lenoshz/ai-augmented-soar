"""Enrichment output models for the AI-Augmented SOAR enrichment service.

These models represent the structured output after an alert has been
processed through the AI enrichment pipeline.
"""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class AlertContext(BaseModel):
    """MITRE ATT&CK classification and contextual enrichment data for an alert."""

    mitre_tactic: str = Field(default="Unknown", description="MITRE ATT&CK tactic name")
    mitre_tactic_id: str = Field(default="Unknown", description="MITRE ATT&CK tactic ID (e.g. TA0002)")
    mitre_technique: str = Field(default="Unknown", description="MITRE ATT&CK technique name")
    mitre_technique_id: str = Field(default="Unknown", description="MITRE ATT&CK technique ID (e.g. T1059.001)")
    asset_owner: Optional[str] = Field(default=None, description="Business owner of the affected asset")
    asset_criticality: Optional[str] = Field(default=None, description="Criticality level of the affected asset")
    ioc_hits: list[str] = Field(default_factory=list, description="Matched indicators of compromise")
    similar_alert_count: int = Field(default=0, description="Number of similar alerts in the last 7 days")


class ResponseSuggestion(BaseModel):
    """AI-generated response suggestion for an enriched alert."""

    immediate_actions: list[str] = Field(
        default_factory=list, description="Immediate containment and triage steps"
    )
    investigation_steps: list[str] = Field(
        default_factory=list, description="Steps for deeper investigation"
    )
    escalation_criteria: str = Field(
        default="", description="Conditions under which the alert should be escalated"
    )
    eql_hunt_query: str = Field(
        default="", description="EQL threat hunting query to look for related activity"
    )


class EnrichedAlert(BaseModel):
    """Fully enriched alert combining original alert data with AI analysis.

    This is the primary output model of the enrichment pipeline, written to
    the ai-augmented-soar-enriched Elasticsearch index.
    """

    # Original alert fields
    alert_id: str = Field(description="Unique identifier for the alert")
    rule_name: str = Field(description="Name of the detection rule that fired")
    severity: str = Field(description="Alert severity level")
    timestamp: str = Field(description="Original alert timestamp")

    # AI-generated enrichment
    summary: str = Field(default="", description="AI-generated plain-language summary of the alert")
    context: AlertContext = Field(default_factory=AlertContext, description="Contextual enrichment data")
    response: ResponseSuggestion = Field(
        default_factory=ResponseSuggestion, description="AI-generated response suggestions"
    )

    # Enrichment metadata
    enriched_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 timestamp when enrichment was completed",
    )
    ai_enriched: bool = Field(default=True, description="Flag indicating this alert has been AI-enriched")
