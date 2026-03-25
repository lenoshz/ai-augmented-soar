#!/usr/bin/env python3
"""Benchmark the enrichment service /api/v1/enrich endpoint.

Usage:
    python benchmark.py [--alerts N]

Measures latency statistics for concurrent enrichment requests.
"""

import argparse
import asyncio
import json
import statistics
import time
from pathlib import Path

import httpx

ENRICHMENT_URL = "http://localhost:8000/api/v1/enrich"
FIXTURES_PATH = Path(__file__).parent.parent / "enrichment-service" / "tests" / "fixtures" / "sample_alerts.json"
CONCURRENCY_LIMIT = 5
LATENCY_TARGET_P95_S = 5.0


async def enrich_one(
    client: httpx.AsyncClient,
    alert: dict,
    semaphore: asyncio.Semaphore,
) -> dict:
    """Send a single enrichment request and return timing info."""
    async with semaphore:
        start = time.monotonic()
        try:
            response = await client.post(ENRICHMENT_URL, json=alert, timeout=30.0)
            elapsed = time.monotonic() - start
            data = response.json()
            tokens = None
            if isinstance(data, dict):
                tokens = data.get("total_tokens")
            return {
                "success": response.status_code == 200,
                "elapsed": elapsed,
                "tokens": tokens,
                "status_code": response.status_code,
            }
        except Exception as exc:
            elapsed = time.monotonic() - start
            return {"success": False, "elapsed": elapsed, "tokens": None, "error": str(exc)}


async def run_benchmark(alerts_count: int) -> None:
    """Run the benchmark with the given number of alerts."""
    fixtures = json.loads(FIXTURES_PATH.read_text())
    alerts = [dict(fixtures[i % len(fixtures)]) for i in range(alerts_count)]

    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    print(f"🚀  Benchmarking {alerts_count} alerts (concurrency: {CONCURRENCY_LIMIT}) ...")

    async with httpx.AsyncClient() as client:
        tasks = [enrich_one(client, alert, semaphore) for alert in alerts]
        results = await asyncio.gather(*tasks)

    latencies = [r["elapsed"] for r in results]
    successes = sum(1 for r in results if r["success"])
    all_tokens = [r["tokens"] for r in results if r.get("tokens") is not None]

    sorted_latencies = sorted(latencies)

    def percentile(data: list[float], p: float) -> float:
        idx = max(0, int(len(data) * p / 100) - 1)
        return data[idx]

    print(f"\n📊  Results ({successes}/{alerts_count} succeeded):")
    print(f"   Mean:    {statistics.mean(latencies):.2f}s")
    print(f"   P50:     {percentile(sorted_latencies, 50):.2f}s")
    print(f"   P95:     {percentile(sorted_latencies, 95):.2f}s")
    print(f"   P99:     {percentile(sorted_latencies, 99):.2f}s")
    print(f"   Min:     {min(latencies):.2f}s")
    print(f"   Max:     {max(latencies):.2f}s")
    if all_tokens:
        print(f"   Avg tokens: {statistics.mean(all_tokens):.0f}")

    p95 = percentile(sorted_latencies, 95)
    if p95 <= LATENCY_TARGET_P95_S:
        print(f"\n✅  P95 {p95:.2f}s is within target ({LATENCY_TARGET_P95_S}s)")
    else:
        print(f"\n⚠️   P95 {p95:.2f}s exceeds target ({LATENCY_TARGET_P95_S}s)")


def main() -> None:
    """Parse args and run the benchmark."""
    parser = argparse.ArgumentParser(description="Benchmark the enrichment service")
    parser.add_argument("--alerts", type=int, default=20, help="Number of alerts to send (default: 20)")
    args = parser.parse_args()
    asyncio.run(run_benchmark(args.alerts))


if __name__ == "__main__":
    main()
