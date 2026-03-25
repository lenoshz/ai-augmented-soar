#!/usr/bin/env python3
"""Export analyst feedback data from Elasticsearch to CSV.

Usage:
    python export-feedback.py [--days N] [--output PATH]

Queries the ai-augmented-soar-feedback index for feedback submitted
within the last N days and writes results to a CSV file.
"""

import argparse
import csv
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

from elasticsearch import Elasticsearch, NotFoundError

FEEDBACK_INDEX = "ai-augmented-soar-feedback"
CSV_COLUMNS = ["alert_id", "rating", "analyst_id", "module", "timestamp"]


def export_feedback(days: int, output_path: str) -> None:
    """Query feedback from Elasticsearch and write to CSV."""
    es = Elasticsearch(
        hosts=[os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")],
        basic_auth=("elastic", os.getenv("ELASTIC_PASSWORD", "changeme")),
        verify_certs=False,
    )

    print(f"📤  Querying {FEEDBACK_INDEX} for last {days} day(s) ...")

    try:
        result = es.search(
            index=FEEDBACK_INDEX,
            body={
                "size": 10000,
                "sort": [{"timestamp": {"order": "desc"}}],
                "query": {
                    "range": {
                        "timestamp": {"gte": f"now-{days}d"}
                    }
                },
            },
        )
    except NotFoundError:
        print(f"⚠️   Index '{FEEDBACK_INDEX}' does not exist – no data to export.")
        es.close()
        sys.exit(0)
    except Exception as exc:
        print(f"❌  Failed to query Elasticsearch: {exc}", file=sys.stderr)
        es.close()
        sys.exit(1)

    hits = result["hits"]["hits"]
    print(f"   Found {len(hits)} feedback record(s)")

    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for hit in hits:
            writer.writerow({col: hit["_source"].get(col, "") for col in CSV_COLUMNS})

    print(f"✅  Exported {len(hits)} records to {output_path}")
    es.close()


def main() -> None:
    """Parse args and run the export."""
    parser = argparse.ArgumentParser(description="Export analyst feedback to CSV")
    parser.add_argument("--days", type=int, default=30, help="Look back N days (default: 30)")
    parser.add_argument("--output", default="feedback-export.csv", help="Output CSV path")
    args = parser.parse_args()

    export_feedback(args.days, args.output)


if __name__ == "__main__":
    main()
