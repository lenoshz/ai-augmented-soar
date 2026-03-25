"""Async threat intelligence client for the AI-Augmented SOAR enrichment service.

Performs IOC lookups against VirusTotal and AbuseIPDB when the corresponding
feature flags are enabled. Errors are logged as warnings and never raised
to avoid blocking the enrichment pipeline.
"""

import logging
from typing import Any, Optional

import httpx

from config import settings

logger = logging.getLogger("ai-augmented-soar")

VIRUSTOTAL_URL = "https://www.virustotal.com/api/v3"
ABUSEIPDB_URL = "https://api.abuseipdb.com/api/v2"


class ThreatIntelClient:
    """Async client for external threat intelligence lookups."""

    def __init__(self) -> None:
        self._http = httpx.AsyncClient(timeout=10.0)

    async def lookup_ip(self, ip: str) -> list[str]:
        """Look up an IP address in enabled threat intel sources.

        Returns a list of hit strings describing any matches found.
        Returns an empty list if no features are enabled or no hits found.
        """
        hits: list[str] = []

        if settings.enable_virustotal and settings.virustotal_api_key:
            vt_hit = await self._virustotal_ip(ip)
            if vt_hit:
                hits.append(vt_hit)

        if settings.enable_abuseipdb and settings.abuseipdb_api_key:
            abuse_hit = await self._abuseipdb_ip(ip)
            if abuse_hit:
                hits.append(abuse_hit)

        return hits

    async def lookup_hash(self, file_hash: str) -> list[str]:
        """Look up a file hash in enabled threat intel sources.

        Returns a list of hit strings or empty list if no hits or features disabled.
        """
        hits: list[str] = []

        if settings.enable_virustotal and settings.virustotal_api_key:
            vt_hit = await self._virustotal_file(file_hash)
            if vt_hit:
                hits.append(vt_hit)

        return hits

    async def _virustotal_ip(self, ip: str) -> Optional[str]:
        """Query VirusTotal for an IP address reputation."""
        try:
            response = await self._http.get(
                f"{VIRUSTOTAL_URL}/ip_addresses/{ip}",
                headers={"x-apikey": settings.virustotal_api_key},
            )
            if response.status_code == 200:
                data: dict[str, Any] = response.json()
                malicious = (
                    data.get("data", {})
                    .get("attributes", {})
                    .get("last_analysis_stats", {})
                    .get("malicious", 0)
                )
                if malicious > 0:
                    return f"VirusTotal: {ip} flagged malicious by {malicious} vendors"
        except httpx.RequestError as exc:
            logger.warning("VirusTotal IP lookup failed for %s: %s", ip, exc)
        return None

    async def _virustotal_file(self, file_hash: str) -> Optional[str]:
        """Query VirusTotal for a file hash reputation."""
        try:
            response = await self._http.get(
                f"{VIRUSTOTAL_URL}/files/{file_hash}",
                headers={"x-apikey": settings.virustotal_api_key},
            )
            if response.status_code == 200:
                data: dict[str, Any] = response.json()
                malicious = (
                    data.get("data", {})
                    .get("attributes", {})
                    .get("last_analysis_stats", {})
                    .get("malicious", 0)
                )
                if malicious > 0:
                    return f"VirusTotal: hash {file_hash} flagged malicious by {malicious} vendors"
        except httpx.RequestError as exc:
            logger.warning("VirusTotal hash lookup failed for %s: %s", file_hash, exc)
        return None

    async def _abuseipdb_ip(self, ip: str) -> Optional[str]:
        """Query AbuseIPDB for an IP address abuse confidence score."""
        try:
            response = await self._http.get(
                f"{ABUSEIPDB_URL}/check",
                headers={"Key": settings.abuseipdb_api_key, "Accept": "application/json"},
                params={"ipAddress": ip, "maxAgeInDays": 90},
            )
            if response.status_code == 200:
                data: dict[str, Any] = response.json()
                score = data.get("data", {}).get("abuseConfidenceScore", 0)
                if score > 50:
                    return f"AbuseIPDB: {ip} abuse confidence score {score}%"
        except httpx.RequestError as exc:
            logger.warning("AbuseIPDB lookup failed for %s: %s", ip, exc)
        return None

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._http.aclose()
        logger.debug("ThreatIntelClient HTTP client closed")


# Singleton instance
threat_intel_client = ThreatIntelClient()
