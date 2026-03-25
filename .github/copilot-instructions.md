# GitHub Copilot Instructions for ai-augmented-soar

## Stack
- **Backend**: Python 3.11+, FastAPI, Pydantic v2, pydantic-settings, anthropic SDK, elasticsearch-py (async)
- **Frontend**: TypeScript, React 18, @elastic/eui, Kibana Plugin SDK
- **Infrastructure**: Docker Compose, Elasticsearch 8.13, Kibana 8.13, Redis 7
- **AI**: Anthropic Claude via `settings.anthropic_model` (never hardcode model names)

## Naming Conventions
- Project identifier: `ai-augmented-soar` (kebab-case for files, indexes, logger names)
- Classes/types: `AiAugmentedSoar` prefix (PascalCase)
- Variables/functions: `aiAugmentedSoar` prefix where needed (camelCase)
- NEVER use `threatlens`, `ThreatLens`, or any variant thereof

## Module Responsibilities
- `enrichment-service/modules/summariser.py`: AI-powered alert summarization
- `enrichment-service/modules/context_enricher.py`: MITRE ATT&CK classification, asset lookup, IOC enrichment
- `enrichment-service/modules/response_suggester.py`: AI response suggestions and analyst chat
- `enrichment-service/services/anthropic_client.py`: Anthropic SDK wrapper with retry logic
- `enrichment-service/services/elastic_client.py`: Elasticsearch async wrapper
- `enrichment-service/services/mitre_client.py`: MITRE ATT&CK data lookup
- `enrichment-service/services/threat_intel_client.py`: VirusTotal and AbuseIPDB IOC lookups

## Python Guidelines
- Use async/await for all I/O operations
- Use Pydantic v2 models with `Field(description=...)` for all data models
- Format with Black; use type hints everywhere
- Logger: `logging.getLogger("ai-augmented-soar")`
- Settings: always import from `config.settings`

## TypeScript/React Guidelines
- Functional components with hooks only
- Strict TypeScript mode
- Use @elastic/eui components for all UI elements
- Named exports preferred
