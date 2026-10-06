# AkmMotion Production Deployment Requirements

> This document covers the exact requirements for running the production render pipeline
> durably and safely. Read before deploying to Railway, Render.com, or any container platform.

---

## 1. Video Storage — REQUIRED BEFORE LAUNCH

### Problem
Rendered MP4 files are written to the **local container filesystem** at:
```
/app/storage/videos/{job_id}.mp4
```
Container filesystems are **ephemeral**. Every redeploy or restart deletes all rendered videos.
A `video_url` pointing to a deleted file returns `404 Not Found`.

### Required Fix: Railway Persistent Volume

1. In the Railway project dashboard, go to your backend service → **"Volumes"**.
2. Add a new persistent volume:
   - **Mount path**: `/app/storage`
   - **Size**: 1 GB (free tier) or larger depending on usage
3. Add an environment variable to your backend service:
   ```
   STORAGE_DIR=/app/storage
   ```
4. Redeploy. All future renders will write to the persistent volume.

The `video_storage_dir` property in `config.py` automatically resolves to:
```
{STORAGE_DIR}/videos/   → /app/storage/videos/
```

**No code changes are required** — the env var is sufficient.

---

## 2. Production Render Execution: Celery + Redis

### Architecture
```
Frontend
   ↓
FastAPI API (POST /api/v1/render/start/{project_id})
   ↓
Durable PostgreSQL RenderJob (status=queued)
   ↓
Redis Broker (CELERY_BROKER_URL)
   ↓
Celery Worker (video_tasks.render_video_task)
   ↓
FFmpeg (1080×1920 MP4)
   ↓
Persistent Storage (/app/storage/videos)
```

In `ENVIRONMENT=production`, `RENDER_EXECUTION_MODE=celery` is **mandatory**. FastAPI's in-process `BackgroundTasks` is restricted to local development to ensure production render jobs survive container redeployments, web restarts, and horizontal scaling.

### Production Enforcement Rules
- If `ENVIRONMENT=production` and `RENDER_EXECUTION_MODE=background`: The backend startup validation fails fast (`SystemExit(1)`).
- If `RENDER_EXECUTION_MODE=celery` and `CELERY_BROKER_URL` is empty: The backend startup validation fails fast (`SystemExit(1)`).
- Render dispatch fails fast if the Redis broker is unavailable in production (no silent fallback to in-process execution).

### Process Topology
Production deployments require two processes:
1. **Web Service**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
2. **Celery Worker**:
   ```bash
   celery -A app.tasks.celery_app worker --loglevel=info --concurrency=2
   ```

### Stale Job Recovery & Cancellation
- **Stale Job Sweeper**: Jobs stuck in `running` or `pending` longer than 15 minutes without progress can be automatically recovered via `RenderService.recover_stale_jobs(stale_seconds=900)`.
- **Cancellation**: `POST /api/v1/render/cancel/{job_id}` calls `celery_app.control.revoke(job.celery_task_id, terminate=True, signal="SIGTERM")` to cleanly interrupt active FFmpeg worker processes and remove temporary files.

---

## 3. FFmpeg Availability in Production

The `Dockerfile` already installs `ffmpeg` via `apt-get`:
```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    build-essential \
    libpq-dev \
    curl
```

The render engine also falls back to the `imageio-ffmpeg` bundled binary, so FFmpeg is
available even if the system `ffmpeg` is missing.

**No additional configuration needed.**

---

## 4. Environment Variables Checklist

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | ✅ | Neon PostgreSQL async connection string (`postgresql+asyncpg://...`) |
| `JWT_SECRET` | ✅ | Must be ≥ 32 chars, strong random secret |
| `ENVIRONMENT` | ✅ | `production` (enforces HSTS, secure cookies, and mandatory Celery) or `development` |
| `RENDER_EXECUTION_MODE` | ✅ in prod | `celery` (mandatory in production) or `background` (allowed in development) |
| `CELERY_BROKER_URL` | ✅ in prod | Redis broker URI (`redis://...`) required when `RENDER_EXECUTION_MODE=celery` |
| `TIMING_MODE` | ❌ optional | `acoustic` (OpenAI Whisper timestamp alignment) or `heuristic` (Devanagari/Latin syllable pacing, default) |
| `STORAGE_DIR` | ✅ for persistence | Mount path for the persistent volume (e.g. `/app/storage`) |
| `GROQ_API_KEY` | ✅ for AI | Primary Groq API key for script intelligence & scene director |
| `FFMPEG_PATH` | ❌ optional | Override FFmpeg binary path; auto-discovered if unset |
| `OPENAI_API_KEY` | ❌ optional | Required for acoustic audio alignment (`TIMING_MODE=acoustic`) |

---

## 5. Cookie Security in Production

When `ENVIRONMENT=production`, guest session cookies are set with `secure=True`
(HTTPS-only). Ensure the production deployment uses HTTPS (Railway provides this
automatically via its TLS termination proxy).

---

## 6. Quick Deploy Validation

After deploying, verify the render pipeline is working:

```bash
# 1. Health check
curl https://your-backend.up.railway.app/api/v1/health

# 2. Start a render (replace with a real project_id and JWT token)
curl -X POST https://your-backend.up.railway.app/api/v1/render/start/{project_id} \
     -H "Authorization: Bearer {token}"

# 3. Poll status
curl https://your-backend.up.railway.app/api/v1/render/status/{job_id} \
     -H "Authorization: Bearer {token}"

# 4. After completed, verify the MP4 is accessible
curl -I https://your-backend.up.railway.app/api/v1/render/video/{job_id} \
     -H "Authorization: Bearer {token}"
# Expected: HTTP/2 200, content-type: video/mp4, accept-ranges: bytes
```

---

## 7. Post-Deploy Persistent Volume Verification

After attaching the volume and redeploying, SSH into the container and verify:

```bash
# In Railway shell
ls -la /app/storage/videos/
# Should show existing rendered MP4 files if any were created before redeployment
echo $STORAGE_DIR
# Should output: /app/storage
```
