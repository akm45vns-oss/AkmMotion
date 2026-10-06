# BRAIN.MD — AKMMOTION PROJECT MEMORY (SINGLE SOURCE OF TRUTH)

> CRITICAL: This file is the permanent memory of this project.
> Every AI session MUST read this file first, then update it before finishing.
> Never wait for user instructions to update this file.

---

## STARTUP RULE (Every Session)

1. Read brain.md completely
2. Understand the current project state
3. Continue from "Current Context"
4. Perform requested work
5. Update brain.md
6. Respond to the user

---

## Last Updated

- Date: 2026-10-05
- Time: 20:25 IST
- By: Antigravity AI — Principal Engineer Production Release Hardening
- Session Summary: Closed final 86→100 production release hardening across all audit dimensions:
  1. Secure Media Downloader: Replaced full-body buffering with incremental 64 KB chunk streaming in `secure_downloader.py`; aborts immediately upon exceeding `max_bytes` with partial file deletion; validates `Content-Type` against allowed media MIME types; enforces redirect loop detection; blocks unsupported/dangerous schemes (`file://`, `ftp://`, `gopher://`); verifies all redirect destination IPs against SSRF rules.
  2. Production Render Queue: Made Celery + Redis mandatory in `ENVIRONMENT=production` (`RENDER_EXECUTION_MODE=celery`); fast-fails on missing `CELERY_BROKER_URL`; disallows silent fallback to `BackgroundTasks` in production; records `celery_task_id` on `RenderJob`; implements Celery task revocation (`celery_app.control.revoke(terminate=True, signal="SIGTERM")`) for job cancellations; implemented stale job recovery (`RenderService.recover_stale_jobs`).
  3. Distributed Rate Limiter: Implemented Redis-backed atomic Lua sliding-window rate limiter (`DistributedRateLimiter`) with fail-closed policy in production for sensitive auth endpoints when Redis is unreachable, while maintaining seamless process-local fallback for dev.
  4. Word Timing & Subtitles (Dual-Mode): Built canonical schema validation (`validate_word_timings` enforcing non-negative, monotonic, and duration-tolerant intervals); added true acoustic alignment via OpenAI Whisper API (`align_audio_acoustically`) when `TIMING_MODE=acoustic`; upgraded syllable pacing model with Devanagari/Hindi phoneme weighting for `TIMING_MODE=heuristic`; added native ASS karaoke active word highlight tags (`{\c&H00FFFF&\b1}WORD{\r}`).
  5. Frontend Synchronization: Bound HTML5 audio `ontimeupdate` in `VideoPreview.tsx` directly to canonical `word_timings` intervals.
  6. Comprehensive Test Matrix: Expanded `test_production_auth_e2e.py` to 18 automated tests; all 64 backend tests pass; Python compilation 100% clean; Next.js production build 100% clean.

---

## PROJECT IDENTITY

| Field | Value |
|---|---|
| Project Title | AkmMotion |
| Internal Codename | AKMMOTION |
| Type | AI Video Studio — Script to YouTube Shorts & Reels |
| Core Pipeline | Script → AI Scenes → CME Character Consistency → Images → Indian Neural TTS → Subtitles → Timeline → Server FFmpeg 1080x1920 MP4 |
| Frontend Stack | Next.js 14 (App Router) + React 18 + TypeScript + Vanilla CSS / TailwindCSS + Framer Motion + Zustand |
| Backend Stack | FastAPI (Python 3.11+) + SQLAlchemy 2.0 (Async) + Neon PostgreSQL |
| Task Queue | Celery + Redis (Durable production rendering with task revocation and stale job recovery) |
| Audio Engine | Edge-TTS (Indian English `en-IN-PrabhatNeural` / `en-IN-NeerjaNeural`, Hindi `hi-IN-MadhurNeural` / `hi-IN-SwaraNeural`) + Whisper Acoustic Alignment |
| Video Engine | Native Server-Side FFmpeg (1080×1920 H.264 / AAC / ASS Karaoke Subtitles / Pan & Zoom Ken Burns) |
| Database | Neon Serverless PostgreSQL (`ep-wispy-waterfall-ay9ni5ea-pooler.c-5.us-east-2.aws.neon.tech`) |
| Security | JWT Auth, Bcrypt Passwords, IDOR Ownership Enforcement, Session-Isolated Guest Mode, Incremental Streaming Downloader, SSRF-Guarded Image Proxy, Distributed Redis Rate Limiter |
| Quality Standard | 9:16 Vertical (1080×1920 Full HD / 720×1280 HD) |
| Current Status | 🟢 100/100 Production Hardened, Fully Verified & Ready for Release |

---

## CORE PIPELINE SPECIFICATION

1. **Script Input & Scene Generation**: AI Director (`Groq` Llama 3) parses script and generates structured scenes with narration, visual prompts, and camera movements.
2. **Character Memory Engine (CME)**: Locks character visual DNA (facial structure, hair, complexion, attire) and injects into scene prompts across generation.
3. **Visual Generation**: Flux-Realism via Pollinations AI / Unsplash HD fallback, routed through backend SSRF-protected proxy.
4. **Indian Voice Synthesis**: Microsoft Edge Neural TTS generating natural Indian English and Hindi audio with accurate timing.
5. **Timeline & Studio Preview**: Interactive canvas with word-by-word karaoke and styling in 9:16 vertical smartphone frame.
6. **Server-Side FFmpeg Export**: Durable Celery worker / Redis broker generating true 1080×1920 H.264/AAC MP4 videos with Burned-In Subtitles and smooth Ken Burns pan/zoom.

---

## VERIFIED EMPIRICAL STATUS

- **Backend Test Suite**: 64/64 Tests Passing
  - `tests/test_production_auth_e2e.py`: 18/18 passed (Streaming downloader, size limit abort, SSRF redirect loops, Celery production queue, distributed rate limiter, stale job recovery, revocation cancellation, karaoke ASS rendering, HTTP Range 206)
  - `tests/test_security_attacks.py`: 11/11 passed (JWT attacks, tampering, metadata SSRF, SQL injection)
  - `tests/test_script_fidelity.py`: 6/6 passed (Script fidelity invariant, word preservation)
  - `tests/test_proxy_security.py`: 10/10 passed (Image proxy allowlist, IP blocking, CORS)
  - `tests/test_provider_resilience.py`: 5/5 passed (Groq key rotation, fallback TTS)
  - `tests/test_storage_service.py`: 5/5 passed (Path traversal defense, media storage)
  - `tests/test_metrics_observability.py`: 3/3 passed (Prometheus counters, health checks)
  - `tests/test_api.py`: 6/6 passed (Auth, projects, scenes, health)
- **Frontend Build**: 100% Clean
  - `npx tsc --noEmit`: 0 errors
  - `npm run build`: 13 static/dynamic routes compiled successfully

---

## LIVE SERVER ENDPOINTS

### Local Development
- Next.js Frontend: `http://localhost:3000`
- FastAPI Backend: `http://localhost:8000`
- OpenAPI Swagger Docs: `http://localhost:8000/docs`
- Character Studio UI: `http://localhost:3000/characters`

### Production (Cloud)
- Frontend (Vercel): `https://akm-motion.vercel.app`
- Backend (Render): `https://akmmotion-backend.onrender.com`
- Backend Swagger: `https://akmmotion-backend.onrender.com/docs`
- Health Check: `https://akmmotion-backend.onrender.com/api/v1/health`
- UptimeRobot: Monitoring backend every 14 min (zero cold starts)

---

## NEXT AI INSTRUCTIONS

1. Always read brain.md first.
2. Maintain clean core scope: Do NOT add back analytics, fake credits, subscriptions, or health score evaluations.
3. Keep the pipeline centered on high-fidelity Script-to-Video generation.
4. All tests and builds must maintain 100% pass rates.

---

*End of brain.md — Last updated: 2026-10-04 22:25 IST*
