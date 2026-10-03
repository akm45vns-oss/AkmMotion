"""
AkmMotion Bottleneck Diagnostic Experiment Matrix (Phase 2)
Isolates latency sources across:
- Test A: API-only (In-memory endpoints, zero DB/AI/Storage)
- Test B: Database-only (Direct representative queries against Neon PostgreSQL)
- Test C: Redis/Limiter-only (Rate limiter and token validation operations)
- Test D: AI Mocked (FastAPI pipeline with mocked external AI providers)
- Test E: Real Provider (Groq scene analyzer round-trip)
- Test F: Render Engine (FFmpeg 1080x1920 MP4 scene generation)
- Test G: Full Realistic Workflow (Login -> Project -> Scenes -> Edit -> Render Mock -> Download)
"""

import os
import sys
import time
import json
import asyncio
import statistics
from uuid import uuid4
from typing import Dict, Any, List
import httpx
from unittest.mock import patch, AsyncMock
from sqlalchemy import text

BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app.main import app
from app.core.security import create_access_token
from app.db.session import engine, AsyncSessionLocal
from app.repositories.project_repo import ProjectRepository
from app.repositories.scene_repo import SceneRepository
from app.core.rate_limit import limiter
from app.services.render_engine import RenderEngineService


async def test_a_api_only(concurrency: int = 50, total_requests: int = 200) -> Dict[str, Any]:
    """Test A — API-only: Tests endpoint with zero DB/AI/Storage I/O (/health/live)."""
    transport = httpx.ASGITransport(app=app)
    latencies = []
    
    async def worker(n: int):
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            for _ in range(n):
                t0 = time.perf_counter()
                res = await client.get("/health/live")
                latencies.append((time.perf_counter() - t0) * 1000.0)
                assert res.status_code == 200

    t_start = time.perf_counter()
    per_w = total_requests // concurrency
    await asyncio.gather(*[worker(per_w) for _ in range(concurrency)])
    elapsed = time.perf_counter() - t_start

    latencies.sort()
    return {
        "test": "Test A — API-only",
        "concurrency": concurrency,
        "total_requests": len(latencies),
        "elapsed_seconds": round(elapsed, 3),
        "rps": round(len(latencies) / elapsed, 2),
        "latency_p50_ms": round(statistics.median(latencies), 2),
        "latency_p95_ms": round(latencies[int(len(latencies) * 0.95)], 2),
        "latency_p99_ms": round(latencies[int(len(latencies) * 0.99)], 2),
        "notes": "Pure ASGI framework + in-memory response. Zero DB, zero external I/O."
    }


async def test_b_database_only(concurrency: int = 25, total_requests: int = 100) -> Dict[str, Any]:
    """Test B — Database-only: Direct representative queries on Neon PostgreSQL."""
    latencies = []
    fake_user_id = uuid4()

    async def worker(n: int):
        for _ in range(n):
            t0 = time.perf_counter()
            async with AsyncSessionLocal() as session:
                repo = ProjectRepository(session)
                items, count = await repo.list_by_user(user_id=fake_user_id, skip=0, limit=20)
            latencies.append((time.perf_counter() - t0) * 1000.0)

    t_start = time.perf_counter()
    per_w = max(1, total_requests // concurrency)
    await asyncio.gather(*[worker(per_w) for _ in range(concurrency)])
    elapsed = time.perf_counter() - t_start

    latencies.sort()
    return {
        "test": "Test B — Database-only",
        "concurrency": concurrency,
        "total_requests": len(latencies),
        "elapsed_seconds": round(elapsed, 3),
        "rps": round(len(latencies) / elapsed, 2),
        "latency_p50_ms": round(statistics.median(latencies), 2),
        "latency_p95_ms": round(latencies[int(len(latencies) * 0.95)], 2),
        "latency_p99_ms": round(latencies[int(len(latencies) * 0.99)], 2),
        "notes": "Direct async queries (ProjectRepository.list_by_user) over remote TLS."
    }


async def test_c_redis_only(concurrency: int = 50, total_requests: int = 500) -> Dict[str, Any]:
    """Test C — Redis/Limiter-only: Sliding window rate limit key checks."""
    latencies = []

    def worker(n: int, worker_id: int):
        for i in range(n):
            t0 = time.perf_counter()
            allowed = limiter.is_allowed(f"key_{worker_id}_{i % 5}", max_requests=10000, window_seconds=60)
            latencies.append((time.perf_counter() - t0) * 1000.0)

    t_start = time.perf_counter()
    per_w = total_requests // concurrency
    for w in range(concurrency):
        worker(per_w, w)
    elapsed = time.perf_counter() - t_start

    latencies.sort()
    return {
        "test": "Test C — Redis/Limiter-only",
        "concurrency": concurrency,
        "total_requests": len(latencies),
        "elapsed_seconds": round(elapsed, 4),
        "rps": round(len(latencies) / elapsed, 2),
        "latency_p50_ms": round(statistics.median(latencies), 4),
        "latency_p95_ms": round(latencies[int(len(latencies) * 0.95)], 4),
        "latency_p99_ms": round(latencies[int(len(latencies) * 0.99)], 4),
        "notes": "Sliding window rate limit checks in memory."
    }


async def test_d_ai_mocked(concurrency: int = 20, total_requests: int = 40) -> Dict[str, Any]:
    """Test D — AI Mocked: Full FastAPI scene generation endpoint with mock AI response."""
    transport = httpx.ASGITransport(app=app)
    token = create_access_token(subject=str(uuid4()))
    headers = {"Authorization": f"Bearer {token}"}
    latencies = []

    mock_scenes = [
        {"scene_number": 1, "narration": "First scene narration.", "image_prompt": "Prompt 1"},
        {"scene_number": 2, "narration": "Second scene narration.", "image_prompt": "Prompt 2"}
    ]

    with patch("app.services.ai.script_analyzer.ScriptAnalyzerService.analyze_script", new_callable=AsyncMock) as mock_an:
        mock_an.return_value = mock_scenes
        
        async def worker(n: int):
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                for _ in range(n):
                    t0 = time.perf_counter()
                    res = await client.post(
                        "/api/v1/ai/generate-scenes",
                        json={"script": "Test script for AI mock benchmarking.", "style": "Explainer"},
                        headers=headers
                    )
                    latencies.append((time.perf_counter() - t0) * 1000.0)
                    assert res.status_code == 200

        t_start = time.perf_counter()
        per_w = total_requests // concurrency
        await asyncio.gather(*[worker(per_w) for _ in range(concurrency)])
        elapsed = time.perf_counter() - t_start

    latencies.sort()
    return {
        "test": "Test D — AI Mocked",
        "concurrency": concurrency,
        "total_requests": len(latencies),
        "elapsed_seconds": round(elapsed, 3),
        "rps": round(len(latencies) / elapsed, 2),
        "latency_p50_ms": round(statistics.median(latencies), 2),
        "latency_p95_ms": round(latencies[int(len(latencies) * 0.95)], 2),
        "latency_p99_ms": round(latencies[int(len(latencies) * 0.99)], 2),
        "notes": "Application layer, validation, serialization with external provider mocked."
    }


async def test_e_real_provider() -> Dict[str, Any]:
    """Test E — Real Provider: Round-trip to external LLM provider (Groq) if configured."""
    from app.services.ai.script_analyzer import ScriptAnalyzerService
    analyzer = ScriptAnalyzerService()
    groq_mgr = analyzer._get_groq_manager()
    
    if not groq_mgr or not getattr(groq_mgr, "_states", None):
        return {
            "test": "Test E — Real Provider",
            "status": "SKIPPED",
            "notes": "No live external Groq keys configured; heuristic mode active."
        }
    
    latencies = []
    for _ in range(3):
        t0 = time.perf_counter()
        try:
            res = await analyzer.analyze_script("The ancient Indian temple stood majestically atop the mountain.", style="Cinematic")
            latencies.append((time.perf_counter() - t0) * 1000.0)
        except Exception as e:
            latencies.append(9999.0)

    latencies.sort()
    return {
        "test": "Test E — Real Provider (Groq)",
        "samples": len(latencies),
        "latency_p50_ms": round(statistics.median(latencies), 2) if latencies else 0.0,
        "latency_p95_ms": round(max(latencies), 2) if latencies else 0.0,
        "notes": "External AI round-trip latency over public internet."
    }


async def test_f_render_engine(runs: int = 2) -> Dict[str, Any]:
    """Test F — Render: Real FFmpeg 1080x1920 MP4 video synthesis."""
    engine_svc = RenderEngineService()
    try:
        bin_path = engine_svc.get_ffmpeg_binary()
    except Exception as e:
        return {
            "test": "Test F — Render (FFmpeg)",
            "status": "SKIPPED",
            "notes": f"FFmpeg binary not discoverable: {e}"
        }

    import tempfile
    latencies = []
    for _ in range(runs):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = os.path.join(tmpdir, "test_render.mp4")
            t0 = time.perf_counter()
            # Fast test: 1 second black vertical 1080x1920 video
            cmd = [
                "-f", "lavfi",
                "-i", "color=c=black:s=1080x1920:d=1.0:r=30",
                "-f", "lavfi",
                "-i", "anullsrc=r=44100:cl=stereo",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-shortest",
                "-y", out_file
            ]
            ret, _, err = await engine_svc._run_ffmpeg(cmd, timeout=30.0)
            latencies.append((time.perf_counter() - t0) * 1000.0)
            assert ret == 0, f"FFmpeg render failed: {err}"

    return {
        "test": "Test F — Render (FFmpeg)",
        "runs": runs,
        "format": "1080x1920 H.264 / AAC",
        "latency_p50_ms": round(statistics.median(latencies), 2) if latencies else 0.0,
        "notes": "Actual local FFmpeg encoding speed for 1s 1080x1920 video."
    }


async def test_g_full_realistic_workflow() -> Dict[str, Any]:
    """Test G — Full Realistic Workflow: Login -> Project -> Scenes -> Edit -> Status."""
    transport = httpx.ASGITransport(app=app)
    user_id = str(uuid4())
    token = create_access_token(subject=user_id)
    headers = {"Authorization": f"Bearer {token}"}

    step_times = {}
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Step 1: Check Auth / Me
        t0 = time.perf_counter()
        r1 = await client.get("/health/ready", headers=headers)
        step_times["1_readiness"] = round((time.perf_counter() - t0) * 1000.0, 2)

        # Step 2: List User Projects
        t0 = time.perf_counter()
        r2 = await client.get("/api/v1/projects", headers=headers)
        step_times["2_list_projects"] = round((time.perf_counter() - t0) * 1000.0, 2)

        # Step 3: Create Project
        t0 = time.perf_counter()
        r3 = await client.post(
            "/api/v1/projects",
            json={"title": "Benchmark Project", "style": "Explainer", "language": "en"},
            headers=headers
        )
        step_times["3_create_project"] = round((time.perf_counter() - t0) * 1000.0, 2)
        project_id = r3.json().get("id") if r3.status_code == 201 else None

        # Step 4: AI Scene Generation (Mocked for deterministic benchmark)
        if project_id:
            with patch("app.services.ai.script_analyzer.ScriptAnalyzerService.analyze_script", new_callable=AsyncMock) as m:
                m.return_value = [{"scene_number": 1, "narration": "Narration", "image_prompt": "Prompt"}]
                t0 = time.perf_counter()
                r4 = await client.post(
                    "/api/v1/ai/generate-scenes",
                    json={"script": "A short script for testing.", "style": "Explainer"},
                    headers=headers
                )
                step_times["4_generate_scenes"] = round((time.perf_counter() - t0) * 1000.0, 2)

            # Step 5: Clean up project
            t0 = time.perf_counter()
            await client.delete(f"/api/v1/projects/{project_id}", headers=headers)
            step_times["5_delete_project"] = round((time.perf_counter() - t0) * 1000.0, 2)

    total_wf_time = sum(step_times.values())
    return {
        "test": "Test G — Full Realistic Workflow",
        "total_duration_ms": round(total_wf_time, 2),
        "steps_breakdown_ms": step_times,
        "notes": "Step-by-step user lifecycle execution."
    }


async def main():
    print("================================================================================")
    print("  AKMMOTION BOTTLENECK DIAGNOSTIC EXPERIMENT MATRIX (TESTS A - G)               ")
    print("================================================================================")

    print("\n[Running] Test A — API-only (In-memory /health/live)...")
    res_a = await test_a_api_only(concurrency=50, total_requests=200)
    print(f"  -> {res_a['test']}: {res_a['rps']} RPS | p50: {res_a['latency_p50_ms']}ms | p95: {res_a['latency_p95_ms']}ms")

    print("\n[Running] Test C — Redis/Limiter-only...")
    res_c = await test_c_redis_only(concurrency=50, total_requests=500)
    print(f"  -> {res_c['test']}: {res_c['rps']} RPS | p50: {res_c['latency_p50_ms']}ms | p95: {res_c['latency_p95_ms']}ms")

    print("\n[Running] Test D — AI Mocked Endpoint...")
    res_d = await test_d_ai_mocked(concurrency=10, total_requests=20)
    print(f"  -> {res_d['test']}: {res_d['rps']} RPS | p50: {res_d['latency_p50_ms']}ms | p95: {res_d['latency_p95_ms']}ms")

    print("\n[Running] Test E — Real Provider...")
    res_e = await test_e_real_provider()
    print(f"  -> {res_e['test']}: p50: {res_e.get('latency_p50_ms', 'N/A')}ms")

    print("\n[Running] Test F — Render Engine (FFmpeg)...")
    res_f = await test_f_render_engine(runs=2)
    print(f"  -> {res_f['test']}: p50: {res_f.get('latency_p50_ms', 'N/A')}ms")

    print("\n[Running] Test G — Full Realistic Workflow...")
    res_g = await test_g_full_realistic_workflow()
    print(f"  -> {res_g['test']}: Total {res_g['total_duration_ms']}ms | Breakdown: {res_g['steps_breakdown_ms']}")

    print("\n[Running] Test B — Database-only (Neon PostgreSQL)...")
    res_b = await test_b_database_only(concurrency=10, total_requests=20)
    print(f"  -> {res_b['test']}: {res_b['rps']} RPS | p50: {res_b['latency_p50_ms']}ms | p95: {res_b['latency_p95_ms']}ms")

    matrix_results = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "experiments": [res_a, res_b, res_c, res_d, res_e, res_f, res_g]
    }

    out_file = os.path.join(os.path.dirname(__file__), "experiment_matrix_results.json")
    with open(out_file, "w") as f:
        json.dump(matrix_results, f, indent=2)

    print(f"\n[Saved] Diagnostic experiment matrix results saved to: {out_file}")


if __name__ == "__main__":
    asyncio.run(main())
