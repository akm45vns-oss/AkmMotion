# 🎬 AkmMotion — AI Script-to-Video SaaS Platform

AkmMotion is an AI-powered SaaS platform that transforms scripts into vertical 1080×1920 videos (YouTube Shorts, Instagram Reels, TikTok) with animated visual scenes, Character Memory Engine (CME) visual consistency, Indian voiceovers, and synced subtitles.

---

## 🛠️ Tech Stack

### Frontend
- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **Styling:** TailwindCSS + Vanilla CSS
- **Animations:** Framer Motion
- **State Management:** Zustand
- **Preview & Canvas:** HTML5 Canvas Video Preview with Word-by-Word Karaoke Subtitles

### Backend
- **Framework:** FastAPI
- **Language:** Python 3.11+
- **Task Queue:** Celery + Redis (Durable production rendering with task revocation and stale job recovery)
- **ORM:** SQLAlchemy 2.0 (Async)
- **Database:** Neon Serverless PostgreSQL
- **Validation:** Pydantic v2
- **Audio & Subtitles:** Edge-TTS + OpenAI Whisper Acoustic Alignment, Devanagari & Latin syllable pacing model, ASS Karaoke Word Highlighting
- **Video Engine:** Server-Side FFmpeg (1080×1920 H.264 / AAC / ASS Subtitles / Pan & Zoom Ken Burns)
- **Security:** JWT Auth, IDOR Protection, Session-Isolated Guest Mode, Incremental Streaming Media Downloader, SSRF-Guarded Image Proxy, Distributed Redis Rate Limiter

---

## 🚀 Quick Start (Local Development)

### 1. Prerequisites
- Node.js 18+
- Python 3.11+
- FFmpeg installed in PATH
- Redis (Optional for local dev with `RENDER_EXECUTION_MODE=background`; mandatory for production with `RENDER_EXECUTION_MODE=celery`)

### 2. Backend Setup
```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## 🧠 Project Architecture & Documentation

Project memory and single source of truth is maintained in `brain.md`. Complete technical specification is in `PROJECT_MASTER_DOCUMENTATION.md` and production deployment rules are in `DEPLOYMENT.md`.

---

## 🔒 Security & Reliability Hardening
- **Streaming Downloader:** Incremental chunk streaming aborts immediately when `max_bytes` is exceeded, validating content-types and preventing redirect SSRF.
- **Durable Task Queue:** Celery + Redis execution mode in production prevents render aborts on web server redeployments or container restarts.
- **Distributed Rate Limiting:** Atomic Redis Lua sliding-window rate limiting with fail-closed security for authentication endpoints.
- **Acoustic & Heuristic Timings:** Dual-mode word timing architecture with strict boundary validation, Whisper acoustic alignment, and frontend/ASS karaoke synchronization.
- **Row-Level Guest Isolation:** Guest isolation cookies prevent cross-session data leakage.
- **Bcrypt Passwords & JWT Security:** Direct bcrypt password hashing and constant-time token validation.