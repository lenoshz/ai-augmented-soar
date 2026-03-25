"""MITRE ATT&CK data client for the AI-Augmented SOAR enrichment service.

Loads the MITRE ATT&CK Enterprise dataset and provides lookups by
technique ID (e.g. T1059.001) or by fuzzy name matching.
"""

import logging
from typing import Optional

logger = logging.getLogger("ai-augmented-soar")

# Inline ATT&CK data to avoid external download dependency at startup.
# Maps technique_id -> {name, tactic_name, tactic_id}
_ATTACK_DATA: dict[str, dict[str, str]] = {
    "T1059.001": {"name": "PowerShell", "tactic_name": "Execution", "tactic_id": "TA0002"},
    "T1059.003": {"name": "Windows Command Shell", "tactic_name": "Execution", "tactic_id": "TA0002"},
    "T1059.006": {"name": "Python", "tactic_name": "Execution", "tactic_id": "TA0002"},
    "T1078": {"name": "Valid Accounts", "tactic_name": "Defense Evasion", "tactic_id": "TA0005"},
    "T1110": {"name": "Brute Force", "tactic_name": "Credential Access", "tactic_id": "TA0006"},
    "T1110.001": {"name": "Password Guessing", "tactic_name": "Credential Access", "tactic_id": "TA0006"},
    "T1110.003": {"name": "Password Spraying", "tactic_name": "Credential Access", "tactic_id": "TA0006"},
    "T1021.002": {"name": "SMB/Windows Admin Shares", "tactic_name": "Lateral Movement", "tactic_id": "TA0008"},
    "T1048.003": {"name": "Exfiltration Over Unencrypted Non-C2 Protocol", "tactic_name": "Exfiltration", "tactic_id": "TA0010"},
    "T1486": {"name": "Data Encrypted for Impact", "tactic_name": "Impact", "tactic_id": "TA0040"},
    "T1566.001": {"name": "Spearphishing Attachment", "tactic_name": "Initial Access", "tactic_id": "TA0001"},
    "T1190": {"name": "Exploit Public-Facing Application", "tactic_name": "Initial Access", "tactic_id": "TA0001"},
    "T1055": {"name": "Process Injection", "tactic_name": "Defense Evasion", "tactic_id": "TA0005"},
    "T1070.001": {"name": "Clear Windows Event Logs", "tactic_name": "Defense Evasion", "tactic_id": "TA0005"},
    "T1003.001": {"name": "LSASS Memory", "tactic_name": "Credential Access", "tactic_id": "TA0006"},
    "T1071.001": {"name": "Web Protocols", "tactic_name": "Command and Control", "tactic_id": "TA0011"},
    "T1105": {"name": "Ingress Tool Transfer", "tactic_name": "Command and Control", "tactic_id": "TA0011"},
    "T1082": {"name": "System Information Discovery", "tactic_name": "Discovery", "tactic_id": "TA0007"},
    "T1083": {"name": "File and Directory Discovery", "tactic_name": "Discovery", "tactic_id": "TA0007"},
    "T1562.001": {"name": "Disable or Modify Tools", "tactic_name": "Defense Evasion", "tactic_id": "TA0005"},
}

_UNKNOWN = {
    "name": "Unknown",
    "tactic_name": "Unknown",
    "tactic_id": "Unknown",
}


class MitreClient:
    """Client for looking up MITRE ATT&CK techniques and tactics."""

    def __init__(self) -> None:
        self._data = _ATTACK_DATA
        logger.debug("MitreClient initialised with %d techniques", len(self._data))

    def lookup_by_id(self, technique_id: str) -> dict[str, str]:
        """Look up a technique by its ATT&CK ID (e.g. T1059.001).

        Returns a dict with keys: name, tactic_name, tactic_id.
        Falls back to Unknown values if the ID is not found.
        """
        result = self._data.get(technique_id.upper(), None)
        if result is None:
            logger.debug("MITRE technique ID '%s' not found – returning unknown", technique_id)
            return dict(_UNKNOWN)
        return dict(result)

    def lookup_by_name(self, technique_name: str) -> Optional[dict[str, str]]:
        """Fuzzy lookup of a technique by name (case-insensitive substring).

        Returns the first matching technique dict or None if not found.
        """
        name_lower = technique_name.lower()
        for tid, info in self._data.items():
            if name_lower in info["name"].lower():
                return {"technique_id": tid, **info}
        logger.debug("MITRE technique name '%s' not found", technique_name)
        return None


# Singleton instance
mitre_client = MitreClient()
