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

- Date: 2026-09-14
- Time: 18:22 IST
- By: Antigravity AI
- Session Summary: Comprehensive codebase reduction to a clean, focused, high-performance core Script-to-Video pipeline:
  `SCRIPT → AI SCENES → CME / CHARACTER CONSISTENCY → IMAGES → INDIAN TTS → SUBTITLES → TIMELINE/PREVIEW → 1080x1920 MP4 SERVER RENDER`.
  Permanently removed dead/bloat features: Analytics system, Notifications, Fake Credit/Usage system, Subscription boilerplate, Script Health Score evaluator, Auto-Improve modal, 4K/60fps/extra aspect ratios (standardized on 9:16 Vertical), and unhooked Navbar search.
  Cleaned database schema and SQLAlchemy ORM models (removed `voices`, `templates`, `subscriptions`, `credits`, `notifications`, `activity_logs`).
  Fully verified: 26/26 backend tests passing (15 security, 6 API, 5 render pipeline) + Next.js frontend production build and TypeScript typecheck compiling with 0 errors.

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

*End of brain.md — Last updated: 2026-09-14 18:22 IST*
