import os
import sys
import time
import json
import asyncio
import statistics
from uuid import uuid4
from typing import List, Dict, Any
import httpx
import psutil

# Ensure backend root is on sys.path
BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app.main import app
from app.core.security import create_access_token
from app.db.session import engine


async def run_stage(
    stage_name: str,
    concurrency: int,
    requests_per_worker: int,
    token: str
) -> Dict[str, Any]:
    """
    Executes a concurrent load test stage against the FastAPI application.
    Measures RPS, p50, p95, p99 latencies, error rates, CPU, and RAM.
    """
    transport = httpx.ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {token}"}
    latencies: List[float] = []
    status_codes: Dict[int, int] = {}
    errors = 0

    proc = psutil.Process(os.getpid())
    cpu_before = psutil.cpu_percent(interval=None)
    ram_before_mb = proc.memory_info().rss / (1024 * 1024)

    start_time = time.perf_counter()

    async def worker(worker_id: int):
        nonlocal errors
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            endpoints = [
                ("GET", "/health/live", None),
                ("GET", "/health/ready", None),
                ("GET", "/metrics", None),
                ("GET", "/health/stats", None),
                ("GET", "/api/v1/workspaces/organizations", None),
                ("GET", "/api/v1/projects", None)
            ]
            for i in range(requests_per_worker):
                method, path, body = endpoints[(worker_id + i) % len(endpoints)]
                req_start = time.perf_counter()
                try:
                    if method == "GET":
                        res = await client.get(path, headers=headers)
                    else:
                        res = await client.post(path, json=body, headers=headers)
                    dur_ms = (time.perf_counter() - req_start) * 1000.0
                    latencies.append(dur_ms)
                    code = res.status_code
                    status_codes[code] = status_codes.get(code, 0) + 1
                    if code >= 500:
                        errors += 1
                except Exception:
                    dur_ms = (time.perf_counter() - req_start) * 1000.0
                    latencies.append(dur_ms)
                    errors += 1

    tasks = [worker(w) for w in range(concurrency)]
    await asyncio.gather(*tasks)

    elapsed = time.perf_counter() - start_time
    total_requests = len(latencies)
    rps = round(total_requests / elapsed, 2) if elapsed > 0 else 0.0

    cpu_after = psutil.cpu_percent(interval=None)
    ram_after_mb = proc.memory_info().rss / (1024 * 1024)

    latencies.sort()
    p50 = round(statistics.median(latencies), 2) if latencies else 0.0
    p95 = round(latencies[int(len(latencies) * 0.95)], 2) if len(latencies) >= 20 else p50
    p99 = round(latencies[int(len(latencies) * 0.99)], 2) if len(latencies) >= 100 else p95
    min_lat = round(min(latencies), 2) if latencies else 0.0
    max_lat = round(max(latencies), 2) if latencies else 0.0
    error_rate = round((errors / total_requests) * 100.0, 2) if total_requests else 0.0

    return {
        "stage": stage_name,
        "concurrency": concurrency,
        "total_requests": total_requests,
        "elapsed_seconds": round(elapsed, 2),
        "rps": rps,
        "latency_min_ms": min_lat,
        "latency_p50_ms": p50,
        "latency_p95_ms": p95,
        "latency_p99_ms": p99,
        "latency_max_ms": max_lat,
        "error_count": errors,
        "error_rate_pct": error_rate,
        "status_codes": status_codes,
        "ram_mb": round(ram_after_mb, 2),
        "cpu_pct": cpu_after,
    }


async def run_render_concurrency_stage(
    stage_name: str,
    concurrent_requests: int,
    token: str
) -> Dict[str, Any]:
    """
    Simulates concurrent render requests to validate capacity controls and rate limits.
    """
    transport = httpx.ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {token}"}
    fake_project_id = str(uuid4())
    status_codes: Dict[int, int] = {}

    start_time = time.perf_counter()

    async def submit_render(req_idx: int):
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post(f"/api/v1/render/start/{fake_project_id}", headers=headers)
            status_codes[res.status_code] = status_codes.get(res.status_code, 0) + 1

    tasks = [submit_render(i) for i in range(concurrent_requests)]
    await asyncio.gather(*tasks)

    elapsed = time.perf_counter() - start_time

    return {
        "stage": stage_name,
        "concurrent_renders": concurrent_requests,
        "elapsed_seconds": round(elapsed, 2),
        "status_codes": status_codes
    }


async def main():
    print("================================================================================")
    print("  AKMMOTION HIGH-CONCURRENCY LOAD & STRESS BENCHMARK (PRODUCTION READINESS)     ")
    print("================================================================================")

    test_user_id = str(uuid4())
    token = create_access_token(subject=test_user_id)

    stages = [
        ("Tier 1 - Baseline Load", 10, 10),
        ("Tier 2 - Moderate Load", 25, 8),
        ("Tier 3 - Peak SaaS Load", 50, 6),
        ("Tier 4 - Stress / Surge", 100, 4),
        ("Tier 5 - Saturation Stress", 250, 2),
    ]

    results = []
    for stage_name, concurrency, per_worker in stages:
        print(f"\n[Running] {stage_name}: {concurrency} concurrent workers, {per_worker} req/worker ({concurrency * per_worker} total reqs)...")
        stage_result = await run_stage(stage_name, concurrency, per_worker, token)
        results.append(stage_result)
        print(f"  -> RPS: {stage_result['rps']} | p50: {stage_result['latency_p50_ms']}ms | p95: {stage_result['latency_p95_ms']}ms | p99: {stage_result['latency_p99_ms']}ms | Errors: {stage_result['error_rate_pct']}% | RAM: {stage_result['ram_mb']}MB")

    render_stages = [
        ("Render Concurrency - 5", 5),
        ("Render Concurrency - 10", 10),
        ("Render Concurrency - 25", 25),
        ("Render Concurrency - 50", 50),
    ]

    render_results = []
    print("\n--- Render Capacity & Concurrency Protection Stages ---")
    for r_name, count in render_stages:
        r_result = await run_render_concurrency_stage(r_name, count, token)
        render_results.append(r_result)
        print(f"  -> {r_name}: Completed in {r_result['elapsed_seconds']}s | Responses: {r_result['status_codes']}")

    output_data = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "user_concurrency_benchmarks": results,
        "render_concurrency_benchmarks": render_results
    }

    results_path = os.path.join(os.path.dirname(__file__), "benchmark_results.json")
    with open(results_path, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"\n[Saved] Complete benchmark telemetry recorded to: {results_path}")
    print("\n========================= SUMMARY TABLE =========================")
    print(f"{'Concurrency Tier':<25} | {'RPS':<8} | {'p50 (ms)':<10} | {'p95 (ms)':<10} | {'p99 (ms)':<10} | {'Errors':<8} | {'RAM (MB)':<8}")
    print("-" * 90)
    for r in results:
        print(f"{r['stage']:<25} | {r['rps']:<8} | {r['latency_p50_ms']:<10} | {r['latency_p95_ms']:<10} | {r['latency_p99_ms']:<10} | {str(r['error_rate_pct'])+'%':<8} | {r['ram_mb']:<8}")
    print("=================================================================\n")


if __name__ == "__main__":
    asyncio.run(main())
