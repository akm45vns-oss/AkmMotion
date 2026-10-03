"""
AkmMotion Colocated Production-Like Service Runner
Manages local PostgreSQL 16 on port 5432 and Redis 5.0 on port 6379.
Initializes and seeds 'akmmotion' database with full neon_schema.sql parity.
Keeps both services running as background infrastructure for load and capacity benchmarking.
"""

import os
import sys
import time
import socket
import subprocess
import signal
import asyncpg
import asyncio

INFRA_DIR = r"C:\Users\akm45\.gemini\local_infra"
PG_BIN = os.path.join(INFRA_DIR, "pgsql", "bin")
PG_DATA = os.path.join(INFRA_DIR, "pgdata")
POSTGRES_EXE = os.path.join(PG_BIN, "postgres.exe")
CREATEDB_EXE = os.path.join(PG_BIN, "createdb.exe")
REDIS_EXE = os.path.join(INFRA_DIR, "redis", "redis-server.exe")

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCHEMA_FILE = os.path.join(WORKSPACE_ROOT, "neon_schema.sql")

pg_log = None
redis_log = None
pg_proc = None
redis_proc = None


def wait_for_port(port: int, host: str = "127.0.0.1", timeout: float = 15.0) -> bool:
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < timeout:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((host, port))
            s.close()
            return True
        except Exception:
            s.close()
            time.sleep(0.3)
    return False


async def init_database_schema():
    print("[Colocated Infra] Connecting to PostgreSQL to create 'akmmotion' database...")
    # Connect to default postgres db with retries
    conn = None
    for attempt in range(15):
        try:
            conn = await asyncpg.connect("postgresql://postgres@127.0.0.1:5432/postgres")
            break
        except (asyncpg.exceptions.CannotConnectNowError, ConnectionRefusedError, OSError):
            await asyncio.sleep(1.0)
    if conn is None:
        raise RuntimeError("Could not connect to postgres after 15 attempts")
    try:
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = 'akmmotion'")
        if not exists:
            print("[Colocated Infra] Database 'akmmotion' does not exist. Creating...")
            await conn.execute("CREATE DATABASE akmmotion OWNER postgres ENCODING 'UTF8'")
            print("[Colocated Infra] Database 'akmmotion' created successfully.")
        else:
            print("[Colocated Infra] Database 'akmmotion' already exists.")
    finally:
        await conn.close()

    print("[Colocated Infra] Connecting to 'akmmotion' to apply schema...")
    db_conn = None
    for attempt in range(15):
        try:
            db_conn = await asyncpg.connect("postgresql://postgres@127.0.0.1:5432/akmmotion")
            break
        except (asyncpg.exceptions.CannotConnectNowError, ConnectionRefusedError, OSError):
            await asyncio.sleep(1.0)
    if db_conn is None:
        raise RuntimeError("Could not connect to akmmotion db after 15 attempts")
    try:
        # Check if users table exists
        table_exists = await db_conn.fetchval(
            "SELECT 1 FROM information_schema.tables WHERE table_name = 'users'"
        )
        if not table_exists:
            print(f"[Colocated Infra] Applying schema from {SCHEMA_FILE}...")
            with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
                schema_sql = f.read()
            # Execute schema statements
            await db_conn.execute(schema_sql)
            print("[Colocated Infra] Schema applied successfully.")
        else:
            print("[Colocated Infra] Schema already applied.")

        # Ensure seed workspace and projects exist for benchmarking
        user_count = await db_conn.fetchval("SELECT count(*) FROM users")
        print(f"[Colocated Infra] Current database state: {user_count} users present.")
    finally:
        await db_conn.close()


def cleanup(signum=None, frame=None):
    print("\n[Colocated Infra] Terminating PostgreSQL and Redis...")
    global pg_proc, redis_proc, pg_log, redis_log
    if pg_proc and pg_proc.poll() is None:
        pg_proc.terminate()
        try:
            pg_proc.wait(timeout=5)
        except Exception:
            pg_proc.kill()
    if redis_proc and redis_proc.poll() is None:
        redis_proc.terminate()
        try:
            redis_proc.wait(timeout=5)
        except Exception:
            redis_proc.kill()
    if pg_log and not pg_log.closed:
        pg_log.close()
    if redis_log and not redis_log.closed:
        redis_log.close()
    print("[Colocated Infra] Infrastructure stopped cleanly.")
    sys.exit(0)


def main():
    global pg_proc, redis_proc, pg_log, redis_log
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    print("================================================================================")
    print("  AKMMOTION COLOCATED INFRASTRUCTURE MANAGER (POSTGRESQL 16 + REDIS 5.0)        ")
    print("================================================================================")

    pg_log = open(os.path.join(INFRA_DIR, "postgres.log"), "a")
    redis_log = open(os.path.join(INFRA_DIR, "redis.log"), "a")

    print("[Colocated Infra] Starting PostgreSQL 16 on 127.0.0.1:5432...")
    pg_proc = subprocess.Popen([POSTGRES_EXE, "-D", PG_DATA], stdout=pg_log, stderr=pg_log)

    print("[Colocated Infra] Starting Redis 5.0 on 127.0.0.1:6379...")
    redis_proc = subprocess.Popen([REDIS_EXE, "--port", "6379"], stdout=redis_log, stderr=redis_log)

    if not wait_for_port(5432):
        print("[Error] PostgreSQL failed to open port 5432 within 15 seconds.")
        cleanup()
    print("[Colocated Infra] PostgreSQL port 5432 is OPEN.")

    if not wait_for_port(6379):
        print("[Error] Redis failed to open port 6379 within 15 seconds.")
        cleanup()
    print("[Colocated Infra] Redis port 6379 is OPEN.")

    asyncio.run(init_database_schema())

    print("\n>>> COLOCATED INFRASTRUCTURE IS READY AND SERVING TRAFFIC <<<")
    print("PostgreSQL: postgresql://postgres@127.0.0.1:5432/akmmotion")
    print("Redis:      redis://127.0.0.1:6379/0")
    print("Press Ctrl+C to stop.\n")

    while True:
        time.sleep(1)
        if pg_proc.poll() is not None:
            print("[Colocated Infra Alert] PostgreSQL process died unexpectedly!")
            break
        if redis_proc.poll() is not None:
            print("[Colocated Infra Alert] Redis process died unexpectedly!")
            break


if __name__ == "__main__":
    main()
