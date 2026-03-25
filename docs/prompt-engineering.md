# Prompt Engineering Guide

This document describes the prompt design philosophy and implementation for the AI-Augmented SOAR enrichment service.

## Overview

The AI-Augmented SOAR service uses three distinct AI modules, each with carefully designed system prompts that guide the model toward structured, reliable outputs.

## System Prompt Design Principles

### 1. Role-Anchored Prompts
Each system prompt begins with a clear role statement that anchors the model's persona:
- **Summariser**: "You are a senior SOC analyst"
- **Context Enricher**: "You are a MITRE ATT&CK expert"
- **Response Suggester**: "You are a senior incident responder"

Role anchoring improves consistency and reduces hallucination by framing the task within a specific professional context.

### 2. Structured Output Constraints
For modules that require machine-parseable output (context enricher, response suggester), prompts explicitly state:
- The response **must** be valid JSON only
- Exact key names are specified
- Fallback values (`"Unknown"`) are defined for uncertain cases
- No explanatory text outside the JSON is permitted

### 3. Minimal Token Budgets
Token limits are set conservatively to control costs and improve response focus:
- **Summariser**: 256 tokens (2-3 sentence summary)
- **Context Enricher**: 128 tokens (JSON classification only)
- **Response Suggester**: 1024 tokens (structured playbook)
- **Analyst Chat**: 1024 tokens (conversational response)

## Module-Specific Guidance

### Summariser (`modules/summariser.py`)

The summariser prompt focuses on:
1. What happened (the event)
2. Which asset is affected (the target)
3. Why it matters (the impact)
4. Likely adversary intent (the goal)

The user message includes: rule name, severity, host, user, process, command line, description, and tags.

**Example output**: "A PowerShell script with an encoded payload was executed on workstation-042 by user jsmith, bypassing execution policy controls. This is consistent with T1059.001 (PowerShell) used for initial staging or post-exploitation tasks. The encoded command obscures intent and warrants immediate investigation."

### Context Enricher (`modules/context_enricher.py`)

The MITRE prompt uses a JSON-only constraint with explicit fallback:
```
respond ONLY with valid JSON containing exactly these keys:
tactic_name, tactic_id, technique_name, technique_id.
If you cannot determine the classification, use "Unknown".
```

The module handles `json.JSONDecodeError` gracefully and falls back to all-Unknown values, ensuring the pipeline never fails due to model output format issues.

### Response Suggester (`modules/response_suggester.py`)

The response prompt requests a structured playbook with four sections:
- `immediate_actions`: Quick containment steps
- `investigation_steps`: Deeper forensic investigation
- `escalation_criteria`: When to involve a senior analyst or CISO
- `eql_hunt_query`: EQL query for proactive threat hunting

### Analyst Chat (`modules/response_suggester.py`)

The chat prompt injects alert context into the system message so the model has full situational awareness without requiring the analyst to repeat context in every message.

## Testing AI Output Quality

When evaluating prompt changes:

1. **Consistency**: Run the same alert 5× and compare outputs
2. **JSON validity**: Use `json.loads()` to validate structured outputs
3. **Relevance**: Verify MITRE classifications match known alert types
4. **Actionability**: Check that response steps are specific, not generic
5. **Tone**: Summaries should be calm, factual, and analyst-focused

## Iterating on Prompts

1. Update the constant (e.g., `SUMMARISER_SYSTEM_PROMPT`) in the relevant module
2. Run the test suite to verify no regressions: `pytest tests/`
3. Test against sample alerts using the seed script: `python scripts/seed-test-alerts.py`
4. Benchmark latency impact: `python scripts/benchmark.py --alerts 10`

## Anti-Patterns to Avoid

- ❌ **Vague role definitions**: "You are an AI assistant" → too generic
- ❌ **Unconstrained output**: Not specifying JSON format for structured fields
- ❌ **Missing fallback instructions**: Model may hallucinate rather than use "Unknown"
- ❌ **Oversized token budgets**: Wastes cost and often produces verbose, less focused output
- ❌ **Hardcoded model names**: Always use `settings.anthropic_model`
