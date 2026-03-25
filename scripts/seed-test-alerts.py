#!/usr/bin/env python3
"""Seed test alerts into the Elasticsearch .alerts-security.alerts-default index.

Usage:
    python seed-test-alerts.py [--count N] [--types TYPE1 TYPE2 ...]

Requires: python-dotenv, elasticsearch
"""

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import os
from elasticsearch import Elasticsearch

FIXTURES_PATH = Path(__file__).parent.parent / "enrichment-service" / "tests" / "fixtures" / "sample_alerts.json"
TARGET_INDEX = ".alerts-security.alerts-default"


def load_fixtures() -> list[dict]:
    """Load sample alerts from the fixtures file."""
    if not FIXTURES_PATH.exists():
        print(f"❌  Fixtures file not found: {FIXTURES_PATH}", file=sys.stderr)
        sys.exit(1)
    return json.loads(FIXTURES_PATH.read_text())


def seed_alerts(count: int, types: list[str] | None = None) -> None:
    """Seed the specified number of alerts into Elasticsearch."""
    fixtures = load_fixtures()

    if types:
        type_lower = [t.lower() for t in types]
        fixtures = [
            a for a in fixtures
            if any(t in a["rule_name"].lower() for t in type_lower)
        ]
        if not fixtures:
            print(f"⚠️   No fixtures matched types: {types}. Using all fixtures.")
            fixtures = load_fixtures()

    es = Elasticsearch(
        hosts=[os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")],
        basic_auth=("elastic", os.getenv("ELASTIC_PASSWORD", "changeme")),
        verify_certs=False,
    )

    success = 0
    for i in range(count):
        alert = dict(fixtures[i % len(fixtures)])
        alert["alert_id"] = str(uuid.uuid4())
        alert["@timestamp"] = datetime.now(timezone.utc).isoformat()
        alert["timestamp"] = alert["@timestamp"]
        alert["ai_enriched"] = False

        try:
            es.index(index=TARGET_INDEX, id=alert["alert_id"], document=alert)
            success += 1
            print(f"  [{i+1}/{count}] Seeded alert: {alert['rule_name']}")
        except Exception as exc:
            print(f"  [{i+1}/{count}] ❌ Failed: {exc}", file=sys.stderr)

    print(f"\n✅  Seeded {success}/{count} alerts into {TARGET_INDEX}")
    es.close()


def main() -> None:
    """Parse arguments and run the seed process."""
    parser = argparse.ArgumentParser(description="Seed test alerts into Elasticsearch")
    parser.add_argument("--count", type=int, default=10, help="Number of alerts to seed (default: 10)")
    parser.add_argument("--types", nargs="+", help="Filter fixtures by rule type (substring match)")
    args = parser.parse_args()

    print(f"🌱  Seeding {args.count} alert(s) into {TARGET_INDEX} ...")
    seed_alerts(args.count, args.types)


if __name__ == "__main__":
    main()
