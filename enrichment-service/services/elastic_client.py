"""Async Elasticsearch client wrapper for the AI-Augmented SOAR enrichment service.

Provides helper methods for writing enriched alerts and feedback,
and for querying alert data.
"""

import logging
from typing import Any, Optional

from elasticsearch import AsyncElasticsearch

from config import settings

logger = logging.getLogger("ai-augmented-soar")

INDEX_ENRICHED = "ai-augmented-soar-enriched"
INDEX_FEEDBACK = "ai-augmented-soar-feedback"


class ElasticClient:
    """Async Elasticsearch wrapper for SOAR-specific operations."""

    def __init__(self) -> None:
        self._client = AsyncElasticsearch(
            hosts=[settings.elasticsearch_url],
            basic_auth=(settings.elastic_username, settings.elastic_password),
            verify_certs=False,
        )

    async def write_enriched_alert(self, alert_id: str, doc: dict[str, Any]) -> None:
        """Write an enriched alert document to the enriched alerts index."""
        await self._client.index(
            index=INDEX_ENRICHED,
            id=alert_id,
            document=doc,
        )
        logger.debug("Wrote enriched alert %s to %s", alert_id, INDEX_ENRICHED)

    async def write_feedback(self, feedback_id: str, doc: dict[str, Any]) -> None:
        """Write analyst feedback to the feedback index."""
        await self._client.index(
            index=INDEX_FEEDBACK,
            id=feedback_id,
            document=doc,
        )
        logger.debug("Wrote feedback %s to %s", feedback_id, INDEX_FEEDBACK)

    async def get_recent_enriched_alerts(self, size: int = 50) -> list[dict[str, Any]]:
        """Fetch the most recent enriched alerts, sorted newest first."""
        result = await self._client.search(
            index=INDEX_ENRICHED,
            body={
                "size": size,
                "sort": [{"enriched_at": {"order": "desc"}}],
                "query": {"match_all": {}},
            },
        )
        return [hit["_source"] for hit in result["hits"]["hits"]]

    async def count(self, index: str, query: Optional[dict[str, Any]] = None) -> int:
        """Return the document count matching the given query in an index."""
        body: dict[str, Any] = {"query": query} if query else {"query": {"match_all": {}}}
        result = await self._client.count(index=index, body=body)
        return int(result["count"])

    async def close(self) -> None:
        """Close the underlying Elasticsearch connection."""
        await self._client.close()
        logger.debug("Elasticsearch client closed")


# Singleton instance
elastic_client = ElasticClient()


async def get_elastic_client() -> ElasticClient:
    """Convenience function to retrieve the singleton elastic client."""
    return elastic_client
