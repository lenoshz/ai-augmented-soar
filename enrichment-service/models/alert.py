"""Alert payload model for incoming security alert data.

Represents the alert structure received from Elasticsearch watcher
or direct API calls to the enrichment service.
"""

from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator


class AlertPayload(BaseModel):
    """Incoming alert payload from Elasticsearch or external sources."""

    # Required fields
    alert_id: str = Field(description="Unique identifier for the alert")
    rule_name: str = Field(description="Name of the detection rule that fired")
    severity: str = Field(description="Alert severity: critical, high, medium, or low")
    timestamp: str = Field(description="ISO 8601 timestamp when the alert was generated")

    # Optional contextual fields
    description: Optional[str] = Field(default=None, description="Human-readable description of the alert")
    host_name: Optional[str] = Field(default=None, description="Hostname of the affected asset")
    host_ip: Optional[str] = Field(default=None, description="IP address of the affected host")
    user_name: Optional[str] = Field(default=None, description="Username associated with the alert")
    process_name: Optional[str] = Field(default=None, description="Process name involved in the alert")
    process_command_line: Optional[str] = Field(default=None, description="Full process command line")
    network_destination_ip: Optional[str] = Field(default=None, description="Destination IP address for network alerts")
    network_destination_port: Optional[int] = Field(default=None, description="Destination port for network alerts")
    file_path: Optional[str] = Field(default=None, description="File path associated with the alert")
    tags: list[str] = Field(default_factory=list, description="Detection rule tags (e.g. MITRE ATT&CK tactics)")
    raw_event: Optional[dict[str, Any]] = Field(default=None, description="Raw event data from the source log")

    @field_validator("severity", mode="before")
    @classmethod
    def normalise_severity(cls, v: str) -> str:
        """Normalise severity to lowercase."""
        return v.lower()
