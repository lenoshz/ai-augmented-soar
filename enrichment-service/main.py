"""FastAPI entrypoint for the AI-Augmented SOAR enrichment service.

Exposes REST endpoints for alert enrichment, analyst chat, feedback,
and alert retrieval. Integrates with Anthropic Claude for AI analysis,
Elasticsearch for persistence, and Redis for caching.
"""

import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from fastapi import BackgroundTasks, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import settings
from models.alert import AlertPayload
from models.enrichment import EnrichedAlert
from modules.context_enricher import enrich_alert
from modules.response_suggester import handle_analyst_chat, suggest_response
from modules.summariser import summarise_alert
from services.elastic_client import elastic_client
from services.threat_intel_client import threat_intel_client

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
)
logger = logging.getLogger("ai-augmented-soar")

# ---------------------------------------------------------------------------
# Lifespan and FastAPI application
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    """Manage startup and shutdown of external clients."""
    yield
    logger.info("Shutting down enrichment service – closing clients")
    await elastic_client.close()
    await threat_intel_client.close()


app = FastAPI(
    title="AI-Augmented SOAR Enrichment Service",
    description="AI-powered security alert enrichment using Anthropic Claude and MITRE ATT&CK.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5601"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    """Request body for the analyst chat endpoint."""

    alert_id: str
    alert: AlertPayload
    history: list[dict[str, Any]] = []
    message: str


class FeedbackRequest(BaseModel):
    """Request body for the feedback endpoint."""

    alert_id: str
    rating: str  # "positive" or "negative"
    analyst_id: str = ""
    module: str = ""
    notes: str = ""


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.post("/api/v1/enrich", response_model=EnrichedAlert)
async def enrich(alert: AlertPayload, background_tasks: BackgroundTasks) -> EnrichedAlert:
    """Enrich a security alert with AI analysis and MITRE ATT&CK context.

    Runs the summariser, context enricher, and response suggester in sequence,
    then writes the result to Elasticsearch in the background.
    """
    logger.info("Enriching alert %s (%s)", alert.alert_id, alert.rule_name)

    # Sequential module pipeline
    summary = await summarise_alert(alert)
    context = await enrich_alert(alert)
    response = await suggest_response(alert, context)

    enriched = EnrichedAlert(
        alert_id=alert.alert_id,
        rule_name=alert.rule_name,
        severity=alert.severity,
        timestamp=alert.timestamp,
        summary=summary,
        context=context,
        response=response,
    )

    # Write to Elasticsearch in the background (non-blocking)
    background_tasks.add_task(
        elastic_client.write_enriched_alert,
        alert.alert_id,
        enriched.model_dump(),
    )

    logger.info("Enrichment complete for alert %s", alert.alert_id)
    return enriched


@app.post("/api/v1/chat")
async def chat(request: ChatRequest) -> dict[str, str]:
    """Handle a multi-turn analyst chat message about a specific alert."""
    logger.info("Chat request for alert %s", request.alert_id)

    # Build a minimal AlertContext from available data for chat
    from models.enrichment import AlertContext

    context = AlertContext()

    response_text = await handle_analyst_chat(
        alert=request.alert,
        context=context,
        history=request.history,
        user_message=request.message,
    )
    return {"response": response_text}


@app.post("/api/v1/feedback")
async def feedback(request: FeedbackRequest) -> dict[str, str]:
    """Record analyst feedback for an enriched alert.

    Only writes feedback if the ENABLE_FEEDBACK_LOOP feature flag is enabled.
    """
    if not settings.enable_feedback_loop:
        logger.debug("Feedback loop disabled – ignoring feedback for alert %s", request.alert_id)
        return {"status": "disabled"}

    feedback_doc = {
        "alert_id": request.alert_id,
        "rating": request.rating,
        "analyst_id": request.analyst_id,
        "module": request.module,
        "notes": request.notes,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    feedback_id = str(uuid.uuid4())
    await elastic_client.write_feedback(feedback_id, feedback_doc)
    logger.info("Recorded feedback for alert %s (rating: %s)", request.alert_id, request.rating)
    return {"status": "recorded", "feedback_id": feedback_id}


@app.get("/api/v1/alerts/enriched")
async def get_enriched_alerts() -> list[dict[str, Any]]:
    """Retrieve the most recent enriched alerts from Elasticsearch."""
    alerts = await elastic_client.get_recent_enriched_alerts()
    return alerts


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint returning service status and configured model."""
    return {
        "status": "healthy",
        "service": "ai-augmented-soar-enrichment",
        "model": settings.anthropic_model,
    }


