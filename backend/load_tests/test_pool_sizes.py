"""
AkmMotion Database Pool Sizing Sensitivity Benchmark
Tests pool configurations under controlled 50-concurrency load on Colocated PostgreSQL:
- Config 1: pool_size=5, max_overflow=5 (10 max)
- Config 2: pool_size=10, max_overflow=10 (20 max)
- Config 3: pool_size=20, max_overflow=20 (40 max)
- Config 4: pool_size=40, max_overflow=20 (60 max)

Measures:
- Throughput (RPS)
- p50, p95, p99 latencies
- Peak DB connections checked out
- Pool queue wait duration
- CPU utilization %
"""

import os
import sys
import time
import json
import asyncio
import statistics
from typing import Dict, Any, List
import psutil
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

LOCAL_DB_URL = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/akmmotion"


async def benchmark_pool_config(
    pool_size: int,
    max_overflow: int,
    concurrency: int = 50,
    requests_per_worker: int = 20
) -> Dict[str, Any]:
    engine = create_async_engine(
        LOCAL_DB_URL,
        echo=False,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=30.0,
        pool_recycle=300,
        pool_pre_ping=True
    )
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    latencies: List[float] = []
    queue_waits: List[float] = []
    errors = 0

    proc = psutil.Process(os.getpid())
    cpu_before = psutil.cpu_percent(interval=None)

    async def worker(worker_id: int):
        nonlocal errors
        for i in range(requests_per_worker):
            t_req = time.perf_counter()
            try:
                # Measure pool checkout wait
                t_checkout = time.perf_counter()
                async with async_session() as session:
                    queue_wait = (time.perf_counter() - t_checkout) * 1000.0
                    queue_waits.append(queue_wait)

                    # Representative mixed query: JOIN projects + scripts
                    res = await session.execute(text("""
                        SELECT p.id, p.title, s.id as script_id, s.content 
                        FROM projects p 
                        LEFT JOIN scripts s ON s.project_id = p.id 
                        LIMIT 10
                    """))
                    rows = res.fetchall()
                    dur = (time.perf_counter() - t_req) * 1000.0
                    latencies.append(dur)
            except Exception as e:
                errors += 1

    t0 = time.perf_counter()
    tasks = [worker(w) for w in range(concurrency)]
    await asyncio.gather(*tasks)
    elapsed = time.perf_counter() - t0

    cpu_after = psutil.cpu_percent(interval=None)
    total_requests = len(latencies)
    rps = round(total_requests / elapsed, 2) if elapsed > 0 else 0.0

    latencies.sort()
    queue_waits.sort()

    def stats(arr: List[float]) -> Dict[str, float]:
        if not arr:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0}
        return {
            "p50": round(statistics.median(arr), 2),
            "p95": round(arr[int(len(arr)*0.95)], 2) if len(arr) >= 20 else arr[-1],
            "p99": round(arr[int(len(arr)*0.99)], 2) if len(arr) >= 100 else arr[-1]
        }

    pool_status = engine.pool.status()
    await engine.dispose()

    return {
        "pool_size": pool_size,
        "max_overflow": max_overflow,
        "total_capacity": pool_size + max_overflow,
        "concurrency": concurrency,
        "total_requests": total_requests,
        "elapsed_seconds": round(elapsed, 2),
        "rps": rps,
        "latency_p50_ms": stats(latencies)["p50"],
        "latency_p95_ms": stats(latencies)["p95"],
        "latency_p99_ms": stats(latencies)["p99"],
        "queue_wait_p50_ms": stats(queue_waits)["p50"],
        "queue_wait_p95_ms": stats(queue_waits)["p95"],
        "error_count": errors,
        "cpu_pct": cpu_after,
        "pool_status_at_end": pool_status
    }


async def main():
    print("================================================================================")
    print("  AKMMOTION DATABASE POOL SIZING SENSITIVITY BENCHMARK                          ")
    print("================================================================================")

    configs = [
        (5, 5),    # 10 max
        (10, 10),  # 20 max
        (20, 20),  # 40 max
        (40, 20),  # 60 max
    ]

    results = []
    for p_size, max_over in configs:
        print(f"\n[Benchmarking] pool_size={p_size}, max_overflow={max_over} (capacity {p_size+max_over})...")
        res = await benchmark_pool_config(p_size, max_over, concurrency=50, requests_per_worker=20)
        results.append(res)
        print(f"  -> RPS: {res['rps']} | p50: {res['latency_p50_ms']}ms | p95: {res['latency_p95_ms']}ms | Queue Wait p95: {res['queue_wait_p95_ms']}ms | CPU: {res['cpu_pct']}%")

    out_file = os.path.join(os.path.dirname(__file__), "pool_size_benchmark_results.json")
    with open(out_file, "w") as f:
        json.dump({"timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "results": results}, f, indent=2)

    print(f"\n[Saved] Pool sizing benchmark results written to {out_file}")


if __name__ == "__main__":
    asyncio.run(main())
