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

## 2. Background Execution — KNOWN LIMITATION

### Current Architecture
```
POST /render/start → FastAPI BackgroundTasks → execute_render_background → FFmpeg
```

`FastAPI BackgroundTasks` runs **inside the uvicorn ASGI event loop**. This means:

| Risk | Reality |
|------|---------|
| Render survives a redeploy? | ❌ **No** — uvicorn process is killed |
| Render survives container restart? | ❌ **No** |
| Jobs retry automatically on failure? | ❌ **No** |
| Render works if process stays alive? | ✅ **Yes** |

### When This Is Acceptable
- Renders complete in < 2 minutes (typical for 1–5 scenes)
- Deploys are infrequent / done during low-traffic windows
- Failed jobs show `status=failed` and users can re-trigger from the frontend

### When This Becomes a Problem
- Long renders (10+ scene projects, 10+ minute renders)
- High-frequency deploys (CI/CD on every commit)
- User-facing SLA requirements on render completion

### Upgrade Path: Celery + Redis

If durable background execution is required, the codebase already has `backend/app/tasks/celery_app.py`
configured correctly with a 10-minute task timeout.

**Steps to enable:**

1. **Add a free Redis instance** (e.g., Railway Redis add-on, Upstash free tier):
   ```
   CELERY_BROKER_URL=redis://your-redis-host:6379/0
   CELERY_RESULT_BACKEND=redis://your-redis-host:6379/0
   ```

2. **Add a Celery task** wrapping `execute_render_background` in `celery_app.py`.

3. **Update `railway.json`** to start both the web server and the Celery worker:
   ```json
   {
     "deploy": {
       "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT & celery -A app.tasks.celery_app worker --loglevel=info"
     }
   }
   ```

4. **Update `render_service.py`** to call `celery_task.delay(...)` instead of
   `background_tasks.add_task(...)`.

> ⚠️ **Do not enable Celery without first testing the Redis connection** in your staging
> environment. An unreachable broker will block render job dispatch.

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
| `DATABASE_URL` | ✅ | Neon PostgreSQL async connection string |
| `JWT_SECRET` | ✅ | Must be ≥ 32 chars, strong random value |
| `STORAGE_DIR` | ✅ for persistence | Mount path for the persistent volume (e.g. `/app/storage`) |
| `FFMPEG_PATH` | ❌ optional | Override FFmpeg binary path; auto-discovered if unset |
| `CELERY_BROKER_URL` | ❌ optional | Required only if upgrading to Celery |
| `GROQ_API_KEY` | ✅ for AI | Primary Groq API key for script intelligence |
| `ENVIRONMENT` | ✅ | Set to `production` to enable secure cookie flags |

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
