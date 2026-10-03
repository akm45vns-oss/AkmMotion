"""
AkmMotion Multi-Worker Performance Benchmark
Tests Uvicorn ASGI server with:
- 1 worker
- 2 workers
- 4 workers
- 8 workers

Measures under controlled load (50 concurrent clients, 200 requests):
- Sustained Throughput (RPS)
- p95 and p99 latencies
- Overall CPU utilization %
- Total Process RAM (MB)
- DB Connection Behavior
"""

import os
import sys
import time
import json
import asyncio
import subprocess
import socket
import statistics
from typing import Dict, Any, List
import httpx
import psutil

BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app.core.security import create_access_token

PORT = 8005
BASE_URL = f"http://127.0.0.1:{PORT}"


def wait_for_server(port: int = PORT, timeout: float = 20.0) -> bool:
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < timeout:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect(("127.0.0.1", port))
            s.close()
            return True
        except Exception:
            s.close()
            time.sleep(0.3)
    return False


async def execute_load(concurrency: int = 50, requests_per_worker: int = 4, token: str = "") -> Dict[str, Any]:
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

    async def worker(w_id: int):
        nonlocal errors
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=15.0) as client:
            for i in range(requests_per_worker):
                path = endpoints[(w_id + i) % len(endpoints)]
                t_start = time.perf_counter()
                try:
                    res = await client.get(path, headers=headers)
                    dur = (time.perf_counter() - t_start) * 1000.0
                    latencies.append(dur)
                    status_codes[res.status_code] = status_codes.get(res.status_code, 0) + 1
                    if res.status_code >= 500:
                        errors += 1
                except Exception:
                    dur = (time.perf_counter() - t_start) * 1000.0
                    latencies.append(dur)
                    errors += 1

    t0 = time.perf_counter()
    tasks = [worker(w) for w in range(concurrency)]
    await asyncio.gather(*tasks)
    elapsed = time.perf_counter() - t0

    total_reqs = len(latencies)
    rps = round(total_reqs / elapsed, 2) if elapsed > 0 else 0.0

    latencies.sort()
    p50 = round(statistics.median(latencies), 2) if latencies else 0.0
    p95 = round(latencies[int(len(latencies)*0.95)], 2) if len(latencies) >= 20 else p50
    p99 = round(latencies[int(len(latencies)*0.99)], 2) if len(latencies) >= 100 else p95

    return {
        "total_requests": total_reqs,
        "elapsed_seconds": round(elapsed, 2),
        "rps": rps,
        "p50_ms": p50,
        "p95_ms": p95,
        "p99_ms": p99,
        "error_count": errors,
        "status_codes": status_codes
    }


def get_process_tree_resources(parent_pid: int) -> Dict[str, float]:
    try:
        parent = psutil.Process(parent_pid)
        children = parent.children(recursive=True)
        total_ram = parent.memory_info().rss
        for c in children:
            try:
                total_ram += c.memory_info().rss
            except Exception:
                pass
        return {"ram_mb": round(total_ram / (1024 * 1024), 2)}
    except Exception:
        return {"ram_mb": 0.0}


def kill_proc_tree(pid: int):
    try:
        parent = psutil.Process(pid)
        for child in parent.children(recursive=True):
            child.kill()
        parent.kill()
    except Exception:
        pass


async def main():
    print("================================================================================")
    print("  AKMMOTION MULTI-WORKER HORIZONTAL SCALING BENCHMARK                           ")
    print("================================================================================")

    token = create_access_token(subject="00000000-0000-0000-0000-000000000001")
    worker_counts = [1, 2, 4, 8]
    results = []

    # Configure app to use local colocated DB for worker test
    env = os.environ.copy()
    env["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/akmmotion"
    env["REDIS_URL"] = "redis://127.0.0.1:6379/0"
    env["CELERY_BROKER_URL"] = "redis://127.0.0.1:6379/0"

    for w_count in worker_counts:
        print(f"\n[Testing] Uvicorn with {w_count} worker(s) on port {PORT}...")
        cmd = [
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", "127.0.0.1",
            "--port", str(PORT),
            "--workers", str(w_count),
            "--log-level", "warning"
        ]
        proc = subprocess.Popen(cmd, cwd=BACKEND_ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if not wait_for_server(PORT, timeout=20.0):
            print(f"  -> Error: Server failed to start with {w_count} workers.")
            kill_proc_tree(proc.pid)
            continue

        time.sleep(1)
        cpu_before = psutil.cpu_percent(interval=None)

        load_metrics = await execute_load(concurrency=50, requests_per_worker=4, token=token)
        cpu_after = psutil.cpu_percent(interval=None)
        res_info = get_process_tree_resources(proc.pid)

        kill_proc_tree(proc.pid)
        time.sleep(1)

        result_entry = {
            "workers": w_count,
            "concurrency": 50,
            "total_requests": load_metrics["total_requests"],
            "rps": load_metrics["rps"],
            "p50_ms": load_metrics["p50_ms"],
            "p95_ms": load_metrics["p95_ms"],
            "p99_ms": load_metrics["p99_ms"],
            "cpu_pct": cpu_after,
            "ram_mb": res_info["ram_mb"],
            "errors": load_metrics["error_count"]
        }
        results.append(result_entry)
        print(f"  -> {w_count} Worker(s): {result_entry['rps']} RPS | p50: {result_entry['p50_ms']}ms | p95: {result_entry['p95_ms']}ms | p99: {result_entry['p99_ms']}ms | CPU: {result_entry['cpu_pct']}% | RAM: {result_entry['ram_mb']}MB")

    out_file = os.path.join(os.path.dirname(__file__), "multi_worker_benchmark_results.json")
    with open(out_file, "w") as f:
        json.dump({"timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "results": results}, f, indent=2)

    print(f"\n[Saved] Multi-worker benchmark recorded to: {out_file}")


if __name__ == "__main__":
    asyncio.run(main())
