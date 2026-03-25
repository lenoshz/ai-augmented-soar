#!/usr/bin/env bash
# Bootstrap script for AI-Augmented SOAR Elastic stack.
# Idempotently creates index templates, imports detection rules,
# and registers the enrichment-trigger watcher.
set -euo pipefail

ELASTIC_PASSWORD="${ELASTIC_PASSWORD:-changeme}"
ELASTICSEARCH_URL="${ELASTICSEARCH_URL:-http://localhost:9200}"
KIBANA_URL="${KIBANA_URL:-http://localhost:5601}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SETUP_DIR="${SCRIPT_DIR}/../setup"

# ---------------------------------------------------------------------------
# Wait for Elasticsearch to be healthy (up to 60 s)
# ---------------------------------------------------------------------------
echo "⏳  Waiting for Elasticsearch at ${ELASTICSEARCH_URL} ..."
for i in $(seq 1 12); do
  STATUS=$(curl -s -u "elastic:${ELASTIC_PASSWORD}" \
    "${ELASTICSEARCH_URL}/_cluster/health" | grep -o '"status":"[^"]*"' | head -1)
  if echo "${STATUS}" | grep -qE '"status":"(green|yellow)"'; then
    echo "✅  Elasticsearch is healthy (${STATUS})"
    break
  fi
  if [ "$i" -eq 12 ]; then
    echo "❌  Elasticsearch did not become healthy within 60 seconds" >&2
    exit 1
  fi
  echo "   Attempt ${i}/12 – waiting 5 s ..."
  sleep 5
done

# ---------------------------------------------------------------------------
# Helper: run curl and exit on failure
# ---------------------------------------------------------------------------
es_curl() {
  local method="$1"; shift
  local url="$1"; shift
  local response
  response=$(curl -s -o /tmp/curl_body -w "%{http_code}" \
    -X "${method}" \
    -u "elastic:${ELASTIC_PASSWORD}" \
    -H "Content-Type: application/json" \
    "${url}" "$@")
  if [ "${response}" -lt 200 ] || [ "${response}" -ge 300 ]; then
    echo "❌  HTTP ${response} for ${method} ${url}" >&2
    cat /tmp/curl_body >&2
    exit 1
  fi
}

kibana_curl() {
  local method="$1"; shift
  local url="$1"; shift
  local response
  response=$(curl -s -o /tmp/curl_body -w "%{http_code}" \
    -X "${method}" \
    -u "elastic:${ELASTIC_PASSWORD}" \
    -H "Content-Type: application/json" \
    -H "kbn-xsrf: true" \
    "${url}" "$@")
  if [ "${response}" -lt 200 ] || [ "${response}" -ge 300 ]; then
    echo "❌  HTTP ${response} for ${method} ${url}" >&2
    cat /tmp/curl_body >&2
    exit 1
  fi
}

# ---------------------------------------------------------------------------
# Create index template: ai-augmented-soar-alerts (30-day hot-warm ILM)
# ---------------------------------------------------------------------------
echo "📋  Creating index template: ai-augmented-soar-alerts ..."
es_curl PUT "${ELASTICSEARCH_URL}/_index_template/ai-augmented-soar-alerts" \
  -d '{
    "index_patterns": ["ai-augmented-soar-alerts-*"],
    "template": {
      "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "index.lifecycle.name": "hot-warm-30d",
        "index.lifecycle.rollover_alias": "ai-augmented-soar-alerts"
      }
    },
    "priority": 100
  }'
echo "✅  Template ai-augmented-soar-alerts created"

# ---------------------------------------------------------------------------
# Create index template: ai-augmented-soar-enriched (90-day hot-warm ILM)
# ---------------------------------------------------------------------------
echo "📋  Creating index template: ai-augmented-soar-enriched ..."
es_curl PUT "${ELASTICSEARCH_URL}/_index_template/ai-augmented-soar-enriched" \
  -d '{
    "index_patterns": ["ai-augmented-soar-enriched-*"],
    "template": {
      "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "index.lifecycle.name": "hot-warm-90d",
        "index.lifecycle.rollover_alias": "ai-augmented-soar-enriched"
      }
    },
    "priority": 100
  }'
echo "✅  Template ai-augmented-soar-enriched created"

# ---------------------------------------------------------------------------
# Import detection rules via Kibana API
# ---------------------------------------------------------------------------
echo "📥  Importing detection rules ..."
if [ -f "${SETUP_DIR}/detection-rules.ndjson" ]; then
  kibana_curl POST "${KIBANA_URL}/api/detection_engine/rules/_import?overwrite=true" \
    -F "file=@${SETUP_DIR}/detection-rules.ndjson;type=application/ndjson"
  echo "✅  Detection rules imported"
else
  echo "⚠️   ${SETUP_DIR}/detection-rules.ndjson not found – skipping rule import"
fi

# ---------------------------------------------------------------------------
# Create watcher: ai-augmented-soar-enrichment-trigger
# ---------------------------------------------------------------------------
echo "⌚  Creating watcher: ai-augmented-soar-enrichment-trigger ..."
if [ -f "${SETUP_DIR}/watcher-trigger.json" ]; then
  es_curl PUT "${ELASTICSEARCH_URL}/_watcher/watch/ai-augmented-soar-enrichment-trigger" \
    -d "@${SETUP_DIR}/watcher-trigger.json"
  echo "✅  Watcher ai-augmented-soar-enrichment-trigger created"
else
  echo "⚠️   ${SETUP_DIR}/watcher-trigger.json not found – skipping watcher creation"
fi

echo ""
echo "🎉  Bootstrap complete!"
