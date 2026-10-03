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
from sqlalchemy import text

# Ensure backend root is on sys.path
BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app.main import app
from app.core.security import create_access_token
from app.db.session import engine


def get_ffmpeg_process_count() -> int:
    """Counts active FFmpeg processes running on the host system."""
    count = 0
    for proc in psutil.process_iter(['name']):
        try:
            name = proc.info.get('name') or ''
            if 'ffmpeg' in name.lower():
                count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return count


async def measure_db_network_latency(samples: int = 3) -> float:
    """Measures raw round-trip ping time to remote PostgreSQL database."""
    latencies = []
    for _ in range(samples):
        t0 = time.perf_counter()
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            latencies.append((time.perf_counter() - t0) * 1000.0)
        except Exception:
            pass
    return round(statistics.median(latencies), 2) if latencies else 0.0


async def get_db_pool_telemetry() -> Dict[str, Any]:
    """Captures SQLAlchemy connection pool state."""
    pool = engine.pool
    return {
        "pool_size": pool.size(),
        "checkedin": pool.checkedin(),
        "checkedout": pool.checkedout(),
        "overflow": pool.overflow()
    }


def get_redis_telemetry() -> Dict[str, Any]:
    """Captures Redis metrics or reports in-memory fallback state."""
    try:
        import redis
        from app.core.config import settings
        r = redis.from_url(settings.REDIS_URL, socket_connect_timeout=0.2)
        info_mem = r.info("memory")
        info_cpu = r.info("cpu")
        return {
            "status": "connected",
            "used_memory_human": info_mem.get("used_memory_human", "N/A"),
            "used_memory_peak_human": info_mem.get("used_memory_peak_human", "N/A"),
            "used_cpu_sys": info_cpu.get("used_cpu_sys", 0.0),
            "used_cpu_user": info_cpu.get("used_cpu_user", 0.0)
        }
    except Exception:
        return {
            "status": "in_memory_fallback",
            "note": "Redis broker unreachable; using thread-safe sliding window in-memory fallback"
        }


def get_celery_telemetry() -> Dict[str, Any]:
    """Captures Celery active workers and queue depth."""
    try:
        from app.tasks.celery_app import celery_app
        insp = celery_app.control.inspect(timeout=0.2)
        active = insp.active() if insp else None
        active_worker_count = len(active) if active else 0
        return {
            "status": "configured",
            "active_workers": active_worker_count,
            "queue_depth": 0
        }
    except Exception:
        return {
            "status": "in_process_fallback",
            "active_workers": 0,
            "queue_depth": 0,
            "note": "Async background tasks running via FastAPI BackgroundTasks"
        }


async def run_baseline_stage(
    stage_name: str,
    concurrency: int,
    requests_per_worker: int,
    token: str
) -> Dict[str, Any]:
    """Executes a concurrent stage and records full system telemetry."""
    transport = httpx.ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {token}"}
    latencies: List[float] = []
    status_codes: Dict[int, int] = {}
    errors = 0

    proc = psutil.Process(os.getpid())
    cpu_before = psutil.cpu_percent(interval=None)
    ram_before_mb = proc.memory_info().rss / (1024 * 1024)

    db_pool_before = await get_db_pool_telemetry()
    db_ping_ms = await measure_db_network_latency(samples=2)

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
    db_pool_after = await get_db_pool_telemetry()
    ffmpeg_processes = get_ffmpeg_process_count()
    redis_telemetry = get_redis_telemetry()
    celery_telemetry = get_celery_telemetry()

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
        "process_ram_mb": round(ram_after_mb, 2),
        "process_cpu_pct": cpu_after,
        "postgres_pool": {
            "before": db_pool_before,
            "after": db_pool_after
        },
        "network_latency_to_db_ms": db_ping_ms,
        "redis_telemetry": redis_telemetry,
        "celery_telemetry": celery_telemetry,
        "active_ffmpeg_processes": ffmpeg_processes
    }


async def main():
    print("================================================================================")
    print("  AKMMOTION PRE-OPTIMIZATION BASELINE CAPTURE (PHASE 1 REPRODUCTION)           ")
    print("================================================================================")

    test_user_id = str(uuid4())
    token = create_access_token(subject=test_user_id)

    stages = [
        ("Tier 1 - Baseline Load", 10, 10),
        ("Tier 2 - Moderate Load", 25, 8),
        ("Tier 3 - Peak SaaS Load", 50, 6),
        ("Tier 4 - Stress / Surge", 100, 4),
    ]

    results = []
    for stage_name, concurrency, per_worker in stages:
        print(f"\n[Benchmarking] {stage_name} ({concurrency} concurrent users, {per_worker} reqs/user)...")
        stage_res = await run_baseline_stage(stage_name, concurrency, per_worker, token)
        results.append(stage_res)
        print(f"  -> RPS: {stage_res['rps']} | p50: {stage_res['latency_p50_ms']}ms | p95: {stage_res['latency_p95_ms']}ms | p99: {stage_res['latency_p99_ms']}ms")
        print(f"  -> DB Latency: {stage_res['network_latency_to_db_ms']}ms | Pool: {stage_res['postgres_pool']['after']} | RAM: {stage_res['process_ram_mb']}MB")

    baseline_data = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "description": "Pre-optimization baseline capturing 10, 25, 50, 100 user concurrency and system metrics",
        "stages": results
    }

    out_file = os.path.join(os.path.dirname(__file__), "baseline_before_optimization.json")
    with open(out_file, "w") as f:
        json.dump(baseline_data, f, indent=2)

    print(f"\n[Saved] Baseline data saved to: {out_file}")


if __name__ == "__main__":
    asyncio.run(main())
