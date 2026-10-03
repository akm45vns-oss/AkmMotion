"""
AkmMotion Database Network Latency Measurement
Compares Development Topology (Remote Neon PostgreSQL AWS US-East-2 Ohio)
vs Production-Like Colocated Topology (Local PostgreSQL on 127.0.0.1:5432).

Measures:
- TCP connection latency
- PostgreSQL connection handshake time
- Simple query latency (SELECT 1)
- Representative SELECT latency (SELECT * FROM projects LIMIT 10)
- Representative JOIN latency (SELECT projects LEFT JOIN scripts LIMIT 10)
- Transaction latency (BEGIN -> INSERT -> ROLLBACK)
"""

import os
import sys
import time
import socket
import statistics
import json
import asyncio
from typing import Dict, Any, List
from urllib.parse import urlparse
import asyncpg

BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app.core.config import settings


def measure_tcp_latency(host: str, port: int, iterations: int = 15) -> Dict[str, float]:
    times = []
    for _ in range(iterations):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10.0)
        t0 = time.perf_counter()
        try:
            s.connect((host, port))
            dt = (time.perf_counter() - t0) * 1000.0
            times.append(dt)
        except Exception as e:
            pass
        finally:
            s.close()
    times.sort()
    return {
        "p50_ms": round(statistics.median(times), 2) if times else 0.0,
        "p95_ms": round(times[int(len(times)*0.95)], 2) if len(times) >= 5 else (times[-1] if times else 0.0),
        "min_ms": round(min(times), 2) if times else 0.0,
        "max_ms": round(max(times), 2) if times else 0.0,
        "samples": len(times)
    }


async def measure_pg_operations(dsn: str, is_remote: bool = False, iterations: int = 15) -> Dict[str, Any]:
    # Normalise asyncpg dsn
    clean_dsn = dsn.replace("postgresql+asyncpg://", "postgresql://")
    parsed = urlparse(clean_dsn)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 5432

    tcp_metrics = measure_tcp_latency(host, port, iterations=iterations)

    conn_times = []
    simple_times = []
    select_times = []
    join_times = []
    tx_times = []

    ssl_mode = "require" if is_remote else False

    for _ in range(iterations):
        # 1. Connection establishment
        t0 = time.perf_counter()
        try:
            conn = await asyncpg.connect(clean_dsn, ssl=ssl_mode, timeout=15.0)
            conn_times.append((time.perf_counter() - t0) * 1000.0)
        except Exception as e:
            continue

        try:
            # 2. Simple query
            t0 = time.perf_counter()
            await conn.fetchval("SELECT 1")
            simple_times.append((time.perf_counter() - t0) * 1000.0)

            # 3. Representative SELECT
            t0 = time.perf_counter()
            await conn.fetch("SELECT id, title, created_at FROM projects ORDER BY created_at DESC LIMIT 10")
            select_times.append((time.perf_counter() - t0) * 1000.0)

            # 4. Representative JOIN
            t0 = time.perf_counter()
            await conn.fetch("""
                SELECT p.id, p.title, s.id as script_id, s.content 
                FROM projects p 
                LEFT JOIN scripts s ON s.project_id = p.id 
                ORDER BY p.created_at DESC LIMIT 10
            """)
            join_times.append((time.perf_counter() - t0) * 1000.0)

            # 5. Transaction
            t0 = time.perf_counter()
            tx = conn.transaction()
            await tx.start()
            await conn.execute("SELECT 1")
            await tx.rollback()
            tx_times.append((time.perf_counter() - t0) * 1000.0)

        finally:
            await conn.close()

    def stats(arr: List[float]) -> Dict[str, float]:
        if not arr:
            return {"p50_ms": 0.0, "p95_ms": 0.0, "min_ms": 0.0, "max_ms": 0.0, "samples": 0}
        arr.sort()
        return {
            "p50_ms": round(statistics.median(arr), 2),
            "p95_ms": round(arr[int(len(arr)*0.95)], 2) if len(arr) >= 5 else arr[-1],
            "min_ms": round(min(arr), 2),
            "max_ms": round(max(arr), 2),
            "samples": len(arr)
        }

    return {
        "host": host,
        "port": port,
        "tcp_latency": tcp_metrics,
        "connection_establishment": stats(conn_times),
        "simple_query_select_1": stats(simple_times),
        "representative_select": stats(select_times),
        "representative_join": stats(join_times),
        "transaction_latency": stats(tx_times)
    }


async def main():
    print("================================================================================")
    print("  AKMMOTION DATABASE NETWORK LATENCY COMPARISON TEST                            ")
    print("================================================================================")

    remote_dsn = settings.DATABASE_URL
    local_dsn = "postgresql://postgres:postgres@127.0.0.1:5432/akmmotion"

    print("\n[1/2] Measuring Development Topology (Remote Neon PostgreSQL in AWS US-East-2)...")
    remote_results = await measure_pg_operations(remote_dsn, is_remote=True, iterations=10)
    print("  TCP Latency p50:", remote_results["tcp_latency"]["p50_ms"], "ms")
    print("  Connection Handshake p50:", remote_results["connection_establishment"]["p50_ms"], "ms")
    print("  Simple Query (SELECT 1) p50:", remote_results["simple_query_select_1"]["p50_ms"], "ms")
    print("  Representative SELECT p50:", remote_results["representative_select"]["p50_ms"], "ms")
    print("  Representative JOIN p50:", remote_results["representative_join"]["p50_ms"], "ms")
    print("  Transaction p50:", remote_results["transaction_latency"]["p50_ms"], "ms")

    print("\n[2/2] Measuring Production-Like Colocated Topology (Local PostgreSQL 127.0.0.1)...")
    local_results = await measure_pg_operations(local_dsn, is_remote=False, iterations=15)
    print("  TCP Latency p50:", local_results["tcp_latency"]["p50_ms"], "ms")
    print("  Connection Handshake p50:", local_results["connection_establishment"]["p50_ms"], "ms")
    print("  Simple Query (SELECT 1) p50:", local_results["simple_query_select_1"]["p50_ms"], "ms")
    print("  Representative SELECT p50:", local_results["representative_select"]["p50_ms"], "ms")
    print("  Representative JOIN p50:", local_results["representative_join"]["p50_ms"], "ms")
    print("  Transaction p50:", local_results["transaction_latency"]["p50_ms"], "ms")

    output = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "development_topology": {
            "name": "Remote Neon Serverless Pooler (AWS US-East-2 Ohio from India Host)",
            "telemetry": remote_results
        },
        "production_colocated_topology": {
            "name": "Colocated PostgreSQL 16 on Loopback (127.0.0.1:5432)",
            "telemetry": local_results
        }
    }

    out_file = os.path.join(os.path.dirname(__file__), "database_latency_comparison.json")
    with open(out_file, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n[Saved] Telemetry written to {out_file}")


if __name__ == "__main__":
    asyncio.run(main())
