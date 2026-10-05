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

- Date: 2026-10-04
- Time: 22:25 IST
- By: Antigravity AI
- Session Summary: Completed exhaustive production audit and remediation across all P0, P1, and P2 findings:
  1. Scrubbed hardcoded DB credentials and live API keys from source code (`config.py`) and `.env` files; added fast-fail startup validation guard for missing secrets.
  2. Fixed critical authentication gap: implemented direct `bcrypt` password hashing on registration and password verification on login; updated `User` model, schemas, and SQL schema to persist `hashed_password`.
  3. Fixed `ai_pipeline_service.py`: added missing `settings` import and aligned Character Memory Engine (CME) dictionary keys (`hair_color`, `outfit`).
  4. Fixed `GroqKeyManager`: updated model constants to active Groq production IDs (`llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, `gemma2-9b-it`).
  5. Hardened `RenderEngineService`: implemented cross-platform FFmpeg path escaping on Windows, eliminated A/V truncation desync by replacing `-shortest` with audio `apad` filter and exact `-t` duration clipping, and added SSRF private IP validation on asset downloads.
  6. Added bounded LRU cache (`_CACHE_MAX_SIZE = 200`) to `VoiceGeneratorService` to eliminate unbounded memory growth.
  7. Added comprehensive automated test suite `tests/test_production_auth_e2e.py` verifying all fixes; all 23 unit, security, and integration tests passing cleanly.

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
| Audio Engine | Edge-TTS (Indian English `en-IN-PrabhatNeural` / `en-IN-NeerjaNeural`, Hindi `hi-IN-MadhurNeural` / `hi-IN-SwaraNeural`) |
| Video Engine | Native Server-Side FFmpeg (1080×1920 H.264 / AAC / ASS Subtitles / Pan & Zoom Ken Burns) |
| Database | Neon Serverless PostgreSQL (`ep-wispy-waterfall-ay9ni5ea-pooler.c-5.us-east-2.aws.neon.tech`) |
| Security | JWT Auth, IDOR Ownership Enforcement, Session-Isolated Guest Mode, SSRF-Guarded Image Proxy |
| Quality Standard | 9:16 Vertical (1080×1920 Full HD / 720×1280 HD) |
| Current Status | 🟢 Fully Streamlined, Verified Production Ready |

---

## CORE PIPELINE SPECIFICATION

1. **Script Input & Scene Generation**: AI Director (`Groq` Llama 3) parses script and generates structured scenes with narration, visual prompts, and camera movements.
2. **Character Memory Engine (CME)**: Locks character visual DNA (facial structure, hair, complexion, attire) and injects into scene prompts across generation.
3. **Visual Generation**: Flux-Realism via Pollinations AI / Unsplash HD fallback, routed through backend SSRF-protected proxy.
4. **Indian Voice Synthesis**: Microsoft Edge Neural TTS generating natural Indian English and Hindi audio with accurate timing.
5. **Timeline & Studio Preview**: Interactive canvas with word-by-word karaoke and styling in 9:16 vertical smartphone frame.
6. **Server-Side FFmpeg Export**: BackgroundTasks / Celery-ready worker generating true 1080×1920 H.264/AAC MP4 videos with Burned-In Subtitles and smooth Ken Burns pan/zoom.

---

## VERIFIED EMPIRICAL STATUS

- **Backend Test Suite**: 26/26 Tests Passing
  - `tests/test_security.py`: 15/15 passed (Guest isolation, IDOR, SSRF proxy blocks, rate limiting)
  - `tests/test_api.py`: 6/6 passed (Auth, projects, scenes, health)
  - `tests/test_render_pipeline.py`: 5/5 passed (Real FFmpeg MP4 generation, multi-scene ffprobe validation, error recovery, concurrency protection, stale job recovery)
- **Frontend Build**: 100% Clean
  - `npx tsc --noEmit`: 0 errors
  - `npm run build`: 12 static/dynamic routes compiled successfully

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
