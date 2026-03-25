# GitHub Copilot Instructions for ai-augmented-soar

## Project Identity
- **Project name**: `ai-augmented-soar` (kebab-case)
- **Class prefix**: `AiAugmentedSoar` (PascalCase)
- **Variable/function prefix**: `aiAugmentedSoar` (camelCase)
- **Logger name**: `logging.getLogger("ai-augmented-soar")`
- **ES indexes**: `ai-augmented-soar-enriched`, `ai-augmented-soar-feedback`, `ai-augmented-soar-alerts`
- ⛔ NEVER use `threatlens`, `ThreatLens`, or any variant

## AI Model Configuration
- Anthropic model name is **always** read from `settings.anthropic_model`
- Never hardcode a model name (e.g., `claude-3-5-sonnet-...`) anywhere except:
  - `.env.example` (as a documentation example)
  - `config.py` default value for `anthropic_model`
- The `/health` endpoint must return `settings.anthropic_model`, not a hardcoded string

## Tech Stack
- **Backend**: Python 3.11+, FastAPI, Pydantic v2, pydantic-settings
- **AI**: `anthropic` SDK (async), model always from `settings.anthropic_model`
- **Data**: `elasticsearch[async]` 8.13, `redis` 5 async client
- **HTTP**: `httpx` (async client for external calls)
- **Frontend**: TypeScript strict mode, React 18, `@elastic/eui`, Kibana Plugin SDK
- **Infrastructure**: Docker Compose, Elasticsearch 8.13, Kibana 8.13, Redis 7

## Python Style Guide
- All I/O must use `async/await`
- Pydantic v2: use `model_dump()`, `model_validate()`, `Field(description=...)`
- Black-compatible formatting (88-char line width)
- Full type hints required — no bare `Any` without comment
- Every module/class must have a docstring stating its purpose
- Import order: stdlib → third-party → internal (config, models, services, modules)

## TypeScript/React Style Guide
- Functional components only (no class components)
- React hooks for all state and side effects
- TypeScript `strict: true` — no `any` without explicit comment
- `@elastic/eui` for all UI elements (no custom CSS where EUI component exists)
- Named exports for all components
- Interface names match the Python model names (e.g., `EnrichedAlert`)

## Module Responsibilities

| Module | File | What it does |
|--------|------|--------------|
| Summariser | `enrichment-service/modules/summariser.py` | 2-3 sentence SOC summary via Claude |
| Context Enricher | `enrichment-service/modules/context_enricher.py` | MITRE classify, asset lookup, IOC check, similar count |
| Response Suggester | `enrichment-service/modules/response_suggester.py` | JSON playbook + multi-turn analyst chat |
| Anthropic Client | `enrichment-service/services/anthropic_client.py` | Async Claude wrapper, retry on 429/529, token tracking |
| Elastic Client | `enrichment-service/services/elastic_client.py` | Async ES: write enriched/feedback, query alerts |
| MITRE Client | `enrichment-service/services/mitre_client.py` | ATT&CK technique/tactic lookups |
| Threat Intel | `enrichment-service/services/threat_intel_client.py` | VirusTotal + AbuseIPDB IOC lookups (feature-flagged) |

## Enrichment Pipeline Order
```
POST /api/v1/enrich
  → summarise_alert()       (max_tokens=256)
  → enrich_alert()          (MITRE + assets + IOC + similar count)
  → suggest_response()      (max_tokens=1024)
  → background write to ES
```

## Testing
- All tests in `enrichment-service/tests/`, runnable with `pytest`
- Mock Anthropic and Elasticsearch in all unit tests
- `asyncio_mode = auto` in `pytest.ini`
- Run with: `ANTHROPIC_API_KEY=test pytest enrichment-service/tests/ -v`

## Common Pitfalls
- Don't raise exceptions in threat intel lookups — log warnings and return empty list
- Always use safe defaults (Unknown, [], 0) when external services fail
- The feedback endpoint must check `settings.enable_feedback_loop` before writing
- Background tasks in FastAPI use `BackgroundTasks.add_task()`, not `asyncio.create_task()`
