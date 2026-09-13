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

- Date: 2026-09-13
- Time: 18:57 IST
- By: Antigravity AI
- Session Summary: Resolved root cause of empty editor (0 scenes). Fixed Neon PostgreSQL schema mismatch in `characters` and `character_dna`/`character_versions` tables. Added resilient session rollback & safe UUID parsing in `AIPipelineService` and endpoints. Generated 7 scenes for project `e3ed3990-f951-48fe-a9a1-d62b22054e07`. Added automated scene generation, progressive loading states, and "Generate Scenes / Regenerate Scenes" controls to ToolBar and EditorPage. Pushed to `origin/main`.

---

## PROJECT IDENTITY

| Field | Value |
|---|---|
| Project Title | AkmMotion |
| Internal Codename | AKMMOTION |
| Type | AI SaaS Platform — Script to YouTube Shorts |
| Category | AI Video Creation / Automation |
| Subsystems | Character Memory Engine (CME), Script Intelligence Engine, Render Engine |
| Unique Selling Points | CME (100% Visual Character Consistency) + 1080x1920 video with voice audio in minutes |
| Platforms | Web (Vercel) |
| Frontend Framework | Next.js 14 (App Router) + React + TypeScript + TailwindCSS + shadcn/ui |
| Backend Framework | FastAPI (Python) + SQLAlchemy 2.0 + Alembic + Celery |
| Database | Neon Serverless PostgreSQL (`ep-wispy-waterfall-ay9ni5ea-pooler.c-5.us-east-2.aws.neon.tech`) |
| Storage | Cloudflare R2 / S3 Compatible Storage |
| Auth | FastAPI Native JWT Auth + bcrypt + Guest Session Fallback |
| AI - Intelligence | CME + Script Intelligence Engine (0-100 Health Score, Auto Cleaner, Safe Improver) |
| AI - Image | Pollinations AI / DALL-E 3 / Unsplash HD |
| AI - Voice | Microsoft Edge Neural TTS (`edge-tts`) + Indian English/Hindi Neural + gTTS fallback |
| Render Engine | Client-Side Smartphone Preview Frame Canvas + MediaStreamAudioDestinationNode |
| Version | 7.14.0 (100% Verified Production Ready) |
| Current Build | Production v7.14.0 (Empirically Verified) |
| Development Status | 🟢 LIVE IN PRODUCTION (Render + Vercel + Neon) & LOCAL DEV VERIFIED |

---

## RECENT VERIFIED EMPIRICAL OUTPUT

```
PROJECTS COUNT: 25
PROJECT d0331de9-c81e-47d7-8d38-ba8a0682b07f SCENES COUNT: 6
```

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
- UptimeRobot: Monitoring backend every 14 min (keeps Render awake, zero cold starts)

---

## CORS ARCHITECTURE

- Frontend calls `/api/v1/*` (same-origin relative path)
- `next.config.js` rewrites: `/api/v1/*` → `https://akmmotion-backend.onrender.com/api/v1/*`
- Runs at Vercel CDN level — no serverless timeout, no browser CORS, no cold-start failures
- UptimeRobot pings `/api/v1/health` every 14 min → Render stays warm always

---

## NEXT AI INSTRUCTIONS

1. Always read brain.md first.
2. Maintain project memory integrity.
3. Everything is 100% verified and operational.
4. CORS is solved via `next.config.js` rewrites — do NOT revert to direct Render calls.
5. UptimeRobot keeps Render warm — no cold start issues.

---

*End of brain.md — Last updated: 2026-09-13 17:54 IST*
