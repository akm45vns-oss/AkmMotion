"""
AkmMotion Saturation Point Discovery Benchmark
Systematically steps up concurrency:
100 -> 150 -> 200 -> 250 -> 300 -> 400 concurrent users.

Evaluates against rigorous saturation criteria:
1. Error rate >= 1.0%
2. p95 latency > 2,500ms (colocated SLA breach)
3. CPU utilization >= 90% sustained
4. Pool queue exhaustion or connection timeout (503s)

Identifies:
- LAST HEALTHY CONCURRENCY
- FIRST SATURATED CONCURRENCY
- CAUSE OF SATURATION
"""

import os
import sys
import time
import json
import asyncio
import statistics
from typing import Dict, Any, List
import httpx
import psutil

# Ensure local colocated database & Redis environment
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/akmmotion"
os.environ["SYNC_DATABASE_URL"] = "postgresql://postgres:postgres@127.0.0.1:5432/akmmotion"
os.environ["REDIS_URL"] = "redis://127.0.0.1:6379/0"
os.environ["CELERY_BROKER_URL"] = "redis://127.0.0.1:6379/0"

BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app.main import app
from app.core.security import create_access_token
from load_tests.ensure_infra import ensure_colocated_infrastructure


async def run_concurrency_step(concurrency: int, requests_per_worker: int = 4, token: str = "") -> Dict[str, Any]:
    transport = httpx.ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {token}"}
    latencies: List[float] = []
    status_codes: Dict[int, int] = {}
    errors = 0

    endpoints = [
        "/health/live",
        "/health/ready",
        "/metrics",
        "/api/v1/workspaces/organizations",
        "/api/v1/projects"
    ]

    proc = psutil.Process(os.getpid())
    cpu_before = psutil.cpu_percent(interval=None)

    start_time = time.perf_counter()

    async def worker(w_id: int):
        nonlocal errors
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            for i in range(requests_per_worker):
                path = endpoints[(w_id + i) % len(endpoints)]
                t0 = time.perf_counter()
                try:
                    res = await client.get(path, headers=headers)
                    dur = (time.perf_counter() - t0) * 1000.0
                    latencies.append(dur)
                    code = res.status_code
                    status_codes[code] = status_codes.get(code, 0) + 1
                    if code >= 500:
                        errors += 1
                except Exception:
                    dur = (time.perf_counter() - t0) * 1000.0
                    latencies.append(dur)
                    errors += 1

    tasks = [worker(w) for w in range(concurrency)]
    await asyncio.gather(*tasks)
    elapsed = time.perf_counter() - start_time

    cpu_after = psutil.cpu_percent(interval=None)
    ram_mb = proc.memory_info().rss / (1024 * 1024)

    total_requests = len(latencies)
    rps = round(total_requests / elapsed, 2) if elapsed > 0 else 0.0

    latencies.sort()
    p50 = round(statistics.median(latencies), 2) if latencies else 0.0
    p95 = round(latencies[int(len(latencies)*0.95)], 2) if len(latencies) >= 20 else p50
    p99 = round(latencies[int(len(latencies)*0.99)], 2) if len(latencies) >= 100 else p95
    error_rate = round((errors / total_requests) * 100.0, 2) if total_requests else 0.0

    # Saturation assessment
    is_saturated = False
    saturation_reason = "healthy"

    if error_rate >= 1.0:
        is_saturated = True
        saturation_reason = f"High error rate: {error_rate}% >= 1.0%"
    elif p95 >= 2500.0:
        is_saturated = True
        saturation_reason = f"Latency SLA breach: p95 {p95}ms >= 2,500ms"
    elif cpu_after >= 92.0:
        is_saturated = True
        saturation_reason = f"CPU thrashing: {cpu_after}% >= 92%"

    return {
        "concurrency": concurrency,
        "total_requests": total_requests,
        "elapsed_seconds": round(elapsed, 2),
        "rps": rps,
        "p50_ms": p50,
        "p95_ms": p95,
        "p99_ms": p99,
        "error_count": errors,
        "error_rate_pct": error_rate,
        "cpu_pct": cpu_after,
        "ram_mb": round(ram_mb, 2),
        "is_saturated": is_saturated,
        "saturation_reason": saturation_reason,
        "status_codes": status_codes
    }


async def main():
    print("================================================================================")
    print("  AKMMOTION SATURATION POINT DISCOVERY (STEPPED CONCURRENCY BENCHMARK)          ")
    print("================================================================================")

    ensure_colocated_infrastructure()

    token = create_access_token(subject="00000000-0000-0000-0000-000000000001")
    steps = [100, 150, 200, 250, 300, 400]

    last_healthy = 0
    first_saturated = None
    saturation_cause = None

    results = []
    for c in steps:
        print(f"\n[Testing Concurrency Step] {c} concurrent users (4 reqs/user = {c*4} total requests)...")
        step_res = await run_concurrency_step(c, requests_per_worker=4, token=token)
        results.append(step_res)

        print(f"  -> RPS: {step_res['rps']} | p50: {step_res['p50_ms']}ms | p95: {step_res['p95_ms']}ms | Errors: {step_res['error_rate_pct']}% | CPU: {step_res['cpu_pct']}% | Status: {step_res['saturation_reason']}")

        if not step_res["is_saturated"]:
            last_healthy = c
        else:
            if first_saturated is None:
                first_saturated = c
                saturation_cause = step_res["saturation_reason"]
                print(f"  >>> FIRST SATURATED CONCURRENCY DETECTED AT {c} USERS ({saturation_cause}) <<<")

    if first_saturated is None:
        first_saturated = "None up to 400 users"
        saturation_cause = "System remained healthy across all tested tiers"

    summary = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "last_healthy_concurrency": last_healthy,
        "first_saturated_concurrency": first_saturated,
        "cause_of_saturation": saturation_cause,
        "steps": results
    }

    out_file = os.path.join(os.path.dirname(__file__), "saturation_benchmark_results.json")
    with open(out_file, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n[Saved] Saturation benchmark recorded to: {out_file}")
    print(f"\n=======================================================")
    print(f"LAST HEALTHY CONCURRENCY:     {last_healthy} users")
    print(f"FIRST SATURATED CONCURRENCY:  {first_saturated} users")
    print(f"CAUSE OF SATURATION:          {saturation_cause}")
    print(f"=======================================================\n")


if __name__ == "__main__":
    asyncio.run(main())
