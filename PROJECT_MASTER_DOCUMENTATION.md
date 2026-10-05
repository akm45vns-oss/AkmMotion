# AkmMotion — Complete Project Architecture, Features & Technical Specification
> **Single-File Master Documentation**  
> **Repository:** `AkmMotion` | **Version:** `6.2.0` | **Date:** 2026-10-04  
> **Classification:** Full Stack AI Video Generation SaaS  

---

## Table of Contents
1. [Executive Summary & Core Philosophy](#1-executive-summary--core-philosophy)
2. [End-to-End System Architecture](#2-end-to-end-system-architecture)
3. [Core Script-to-Video Pipeline Specification](#3-core-script-to-video-pipeline-specification)
4. [Exhaustive Feature Catalog](#4-exhaustive-feature-catalog)
   - 4.1 [Script Analyzer & Director Engine](#41-script-analyzer--director-engine)
   - 4.2 [Character Memory Engine (CME)](#42-character-memory-engine-cme)
   - 4.3 [Indian Neural Voice Synthesis Engine (TTS)](#43-indian-neural-voice-synthesis-engine-tts)
   - 4.4 [Visual Generation & Face Consistency Engine](#44-visual-generation--face-consistency-engine)
   - 4.5 [Studio Editor, Timeline & Interactive Preview](#45-studio-editor-timeline--interactive-preview)
   - 4.6 [Server-Side Native FFmpeg Render Engine](#46-server-side-native-ffmpeg-render-engine)
   - 4.7 [Multi-Tenant Workspaces & Enterprise RBAC](#47-multi-tenant-workspaces--enterprise-rbac)
   - 4.8 [Authentication, Guest Mode & Session Hardening](#48-authentication-guest-mode--session-hardening)
   - 4.9 [Security, SSRF Guard & IDOR Defense](#49-security-ssrf-guard--idor-defense)
   - 4.10 [Observability, Metrics & Health Probing](#410-observability-metrics--health-probing)
5. [Complete Repository Directory & File Structure](#5-complete-repository-directory--file-structure)
6. [Database Schema & Data Model Specification](#6-database-schema--data-model-specification)
7. [REST API Endpoint & Contract Specification](#7-rest-api-endpoint--contract-specification)
8. [Frontend State Management & Component Hierarchy](#8-frontend-state-management--component-hierarchy)
9. [Deployment, Infrastructure & Operations Guide](#9-deployment-infrastructure--operations-guide)
10. [Configuration & Environment Variables Reference](#10-configuration--environment-variables-reference)
11. [Testing, Quality Assurance & Verification Metrics](#11-testing-quality-assurance--verification-metrics)

---

## 1. Executive Summary & Core Philosophy

**AkmMotion** is a vertical-first (9:16, 1080×1920) AI Video Studio engineered specifically for high-retention short-form content: YouTube Shorts, Instagram Reels, and TikTok. 

Unlike generic video generation tools that generate loosely related slides or hallucinate scripts, AkmMotion is built upon a **Strict Script Fidelity Invariant**:
> **Non-Negotiable Pipeline Invariant:**  
> The user's input script is the authoritative, immutable source of truth. The AI Director segments the script across scenes such that the exact concatenation of scene narrations reproduces the user's input word-for-word, token-for-token. The model is forbidden from inventing hooks, omitting lines, rewriting dialogue, or inserting extraneous commentary.

### Key Technology Stack Highlights
| Layer | Technologies |
|---|---|
| **Frontend** | Next.js 14 (App Router), React 18, TypeScript, TailwindCSS, Vanilla CSS, Framer Motion, Lucide Icons, HTML5 Canvas |
| **State & Store** | Zustand (Client video state, active scene, playback scrubber, project metadata) |
| **Backend** | FastAPI (Python 3.11+), AsyncIO, Uvicorn, Pydantic v2 |
| **ORM & Database** | SQLAlchemy 2.0 (Async), asyncpg, Neon Serverless PostgreSQL |
| **AI LLM Routing** | Groq Llama 3 (5-key round-robin rotation & automatic rate-limit failover), OpenAI GPT-3.5 fallback |
| **TTS Engine** | Microsoft Edge Neural TTS (Primary, studio-grade Indian English & Hindi), OpenAI TTS, gTTS |
| **Visual Rendering** | Pollinations AI (Flux-Realism 9:16), Replicate PuLID FaceID, DALL-E 3, Unsplash HD fallback |
| **Video Engine** | Server-side native FFmpeg with Pan & Zoom Ken Burns filters and burned-in karaoke subtitles |
| **Security** | Guest session isolation cookies, JWT access + refresh token families, SSRF-guarded image proxy |

---

## 2. End-to-End System Architecture

```
                                  +-------------------------------------------------------------+
                                  |                     CLIENT BROWSER                          |
                                  |  Next.js 14 App Router (TailwindCSS + Framer Motion)        |
                                  |  - Interactive 9:16 Player (<canvas> / <video> / Web Audio)  |
                                  |  - Visual Timeline Scrubber & Word-by-Word Karaoke          |
                                  |  - Scene Inspector & CME Character Memory Studio            |
                                  +------------------------------+------------------------------+
                                                                 | HTTPS / WSS / REST
                                                                 v
+-------------------------------------------------------------------------------------------------------------------------------+
|                                                FASTAPI BACKEND RUNTIME                                                        |
|                                                                                                                               |
|  [ Middlewares ]                                                                                                              |
|  - Structured Request Logging (X-Request-ID, JSON stdout, Prometheus latency recorder)                                         |
|  - Security Headers (HSTS, nosniff, DENY frame options, strict referrer)                                                      |
|  - CORS Policy (Vercel production regex, localhost)                                                                           |
|  - Performance Profiling Middleware                                                                                           |
|                                                                                                                               |
|  [ Core Controllers / Routers ]                                                                                               |
|  +--------------------+  +--------------------+  +--------------------+  +--------------------+  +-------------------------+  |
|  |   /auth & /user    |  |     /projects      |  |      /scenes       |  |    /characters     |  |       /workspaces       |  |
|  | JWT, Refresh tokens|  | CRUD, Styles, Lang |  | Narration, Motions |  | CME DNA, Locks, Rel|  | Multi-tenant Orgs & RBAC|  |
|  +--------------------+  +--------------------+  +--------------------+  +--------------------+  +-------------------------+  |
|  +--------------------------------------------+  +--------------------------------------------+  +-------------------------+  |
|  |                   /ai                      |  |                  /render                   |  |    /storage & /settings |  |
|  | Groq rotation, Edge-TTS, Image Proxy, Fal  |  | BackgroundTasks, FFmpeg Segment Compiler   |  | Local / R2, User config |  |
|  +--------------------------------------------+  +--------------------------------------------+  +-------------------------+  |
+------------------------------+--------------------------------+-------------------------------+-------------------------------+
                               |                                |                               |
                               v                                v                               v
           +-----------------------------+     +-----------------------------+     +-----------------------------+
           |     POSTGRESQL (NEON)       |     |      EXTERNAL AI SERVICES   |     |    LOCAL / CLOUD STORAGE    |
           | 28 Relational Tables        |     | - Groq Llama 3 (5 Keys)     |     | - Server storage (/storage) |
           | - Users & Refresh Tokens    |     | - Edge-TTS Neural Audio     |     | - Cloudflare R2 / S3        |
           | - Projects, Scripts, Scenes |     | - Pollinations Flux-Realism |     | - Video Renders (.mp4)      |
           | - CME Character Memory DNA  |     | - Replicate PuLID FaceID    |     | - Image & Audio Cache       |
           | - Render Jobs & Video Assets|     | - Fal.ai Text-to-Video      |     +-----------------------------+
           +-----------------------------+     +-----------------------------+
```

---

## 3. Core Script-to-Video Pipeline Specification

The video generation workflow converts raw natural text into a studio-grade MP4 video in 7 deterministic phases:

```
[1. User Script] ──> [2. AI Director Parsing] ──> [3. CME Character Injection] ──> [4. Audio & Word Timings]
                                                                                               │
[7. Final 1080x1920 MP4] <── [6. Server FFmpeg Render] <── [5. Studio Preview & Timeline] <────┘
```

1. **Script Ingestion & Scene Allocation:**
   - Raw user text is analyzed for word count and sentence boundaries.
   - Deterministic scene counting bounds the project duration to 3.0s–10.0s per scene at 2.2 words per second.
2. **AI Director Scene Analysis (Groq Llama 3):**
   - High-speed, multi-key Groq rotation decomposes the script into individual scenes.
   - Each scene receives camera motion (`push`, `pull`, `pan_left`, `pan_right`, `static`), transition type (`cut`, `fade`, `slide`, `zoom`), emotion tag, and an English visual prompt.
   - Script fidelity invariant verification: normalized tokens of original script must strictly match normalized tokens of combined scene narrations.
3. **Character Memory Engine (CME) Locking:**
   - If a character is attached to the project/scene, their visual DNA (facial structure, hair, complexion, clothing, expression) is prepended to the visual prompt.
4. **Visual & Audio Asset Generation:**
   - Visuals are generated at 9:16 vertical resolution via Pollinations Flux-Realism or Replicate PuLID.
   - Indian Neural Voiceover is synthesized via Microsoft Edge TTS (`en-IN-PrabhatNeural`, `hi-IN-SwaraNeural`).
   - Word-level timing timestamps are calculated for real-time karaoke subtitles.
5. **Interactive Studio Review:**
   - The user scrubs the timeline, plays back the canvas in real-time, inspects scene properties, swaps images, or regenerates audio on demand.
6. **FFmpeg Video Compilation:**
   - Individual scene segments are generated with Ken Burns pan/zoom equations, audio streams, and burned-in styled subtitles.
   - Segments are stitched together via FFmpeg concat protocol into a unified 1080×1920 H.264 / AAC MP4 file.
7. **Delivery & Streaming:**
   - Final MP4 is served via HTTP Range requests for in-browser streaming and direct download.

---

## 4. Exhaustive Feature Catalog

### 4.1 Script Analyzer & Director Engine
- **Fidelity Enforcement:**
  - Token normalization algorithm strips punctuation while preserving Devanagari and Latin word boundaries.
  - Verification check: `normalize_tokens(script) == normalize_tokens(sum(scene.narrations))`.
  - Rejection with automatic deterministic fallback if the LLM drops or invents words.
- **Scene Allocation Policy:**
  - 0–20 words: 1 scene (or up to 3 for multiple complete sentences).
  - 21–50 words: 1–2 scenes.
  - 51–100 words: 2–3 scenes.
  - 101–180 words: 3–4 scenes.
  - 181–300 words: 4–6 scenes.
  - 300+ words: adaptive (~40–60 words per scene, capped at 10 scenes).
- **Groq Key Management:**
  - Dynamic 5-key round-robin pool (`GROQ_API_KEY`, `GROQ_API_KEY_2`, etc.).
  - Automatic failure detection with immediate key rotation and fallback to deterministic segmentation.

### 4.2 Character Memory Engine (CME)
- **Visual DNA System:**
  - Tracks 16 physical traits: `skin_tone`, `hair_color`, `hair_style`, `hair_length`, `eye_color`, `face_shape`, `beard`, `mustache`, `body_type`, `height_category`, `outfit`, `shoes`, `expression`, `visual_style`, `lighting_preference`, `camera_preference`.
  - Injects `prompt_prefix`, `prompt_suffix`, and `negative_prompt` into every scene visual generation.
- **Identity Locking & Versioning:**
  - Characters can be locked to prevent accidental prompt mutations.
  - Each edit creates an immutable snapshot in `character_versions` table.
- **Fast In-Memory Cache:**
  - `CharacterCache` delivers character DNA lookups in under 100ms.
- **Consistency Scoring:**
  - Evaluates generated scene visual prompts against character DNA specifications and returns an alignment score (0–100%).

### 4.3 Indian Neural Voice Synthesis Engine (TTS)
- **Voices Supported:**
  - Indian English Male: `en-IN-PrabhatNeural`
  - Indian English Female: `en-IN-NeerjaNeural`
  - Hindi Native Male: `hi-IN-MadhurNeural`
  - Hindi Native Female: `hi-IN-SwaraNeural`
  - Universal Voices: `en-US-GuyNeural`, `en-US-JennyNeural`, `en-US-ChristopherNeural`
- **Audio Caching & Fallbacks:**
  - MD5 hashing of text + voice ID enables 0ms cached replays.
  - Multi-tiered fallback: Edge-TTS $\rightarrow$ OpenAI TTS $\rightarrow$ gTTS $\rightarrow$ Synthesized 0.5s silent MP3 frame (preventing Web Audio API decode crashes).
- **Word-Level Subtitle Synchronization:**
  - Computes millisecond start and end boundaries (`start_ms`, `end_ms`) for each word using a syllable-weighted speech pacing model.
  - Generates timed Advanced SubStation Alpha (`.ass`) subtitle files with 1080×1920 layout and yellow active word styling.
  - *Note on Implementation:* Acoustic phoneme forced-alignment (e.g. via WhisperX or Gentle) is **NOT IMPLEMENTED**; current production timing is calculated via syllable-weighted heuristic estimation.
  - Used for real-time karaoke highlight animations on the frontend preview and ASS subtitle filter burning.

### 4.4 Visual Generation & Face Consistency Engine
- **Flux-Realism (Pollinations AI):**
  - High-fidelity 9:16 vertical images rendered without text overlays.
  - Deterministic seeds derived from prompt hashes prevent duplicate visuals across adjacent scenes.
- **Replicate PuLID / FaceID Integration:**
  - Reference portrait image input locks facial geometry across different action scenes.
- **Curated Visual Styles:**
  - Explainer (Documentary/Realistic)
  - Cinematic (Dramatic lighting, film grain)
  - Story (Warm atmosphere, emotional depth)
  - Vlog (Authentic lifestyle photography)
  - Anime (Makoto Shinkai aesthetic, cel shaded)
  - Finance (Architectural, clean minimalist)

### 4.5 Studio Editor, Timeline & Interactive Preview
- **Canvas Video Player:**
  - Real-time preview within a simulated 9:16 smartphone viewport.
  - Real-time Ken Burns smooth pan and zoom preview using CSS and Framer Motion transforms.
  - Word-by-word karaoke subtitle overlay with glowing yellow active word highlights.
- **Interactive Multi-Track Timeline:**
  - Visual scene cards representing duration and timing.
  - Click-to-scrub playback cursor.
  - Reordering, deleting, and adding scenes.
- **Scene Inspector:**
  - Live editing of narration, visual prompts, duration, camera motion, and animation style.
  - One-click regeneration of individual scene visuals or narration audio.
- **Responsive Workspace Layout:**
  - Desktop: 3-pane layout (Player, Inspector, Timeline).
  - Mobile (< lg screens): Segmented workspace toggle (Player, Inspector, Timeline) with 44px touch targets.

### 4.6 Server-Side Native FFmpeg Render Engine
- **FFmpeg Discovery:**
  - Automatically identifies system `ffmpeg`, user-configured `FFMPEG_PATH`, or fallback `imageio-ffmpeg` binary.
- **Segment Processing Pipeline:**
  1. Image / Video Asset Preparation: Fetches image/video from URL via SSRF-safe downloader, verifies dimensions, or synthesizes high-contrast dark card if missing.
  2. Audio Track Synthesis: Downloads audio or generates Edge-TTS speech with silence fallback.
  3. Ken Burns Filter Execution: Computes exact zoompan expressions for `push`, `zoom_out`, `pan_left`, `pan_right`, and subtle pulse.
  4. Audio/Video Duration Synchronization: Uses `-af apad` and exact `-t {duration:.2f}` clipping (removing legacy `-shortest`) to prevent visual or audio truncation.
  5. Subtitle Burning: Renders ASS timed subtitles via `ass` filter with `drawtext` fallback at the bottom-third of the vertical screen.
  6. Multi-Scene Transitions & Stitching: Renders smooth transitions (`fade`, `slide`, `wipe`, `zoom`) via FFmpeg `xfade` and audio `acrossfade`, automatically falling back to concat demuxer if transitions are disabled or unavailable.
- **Stream Serving:**
  - Completed videos are streamed via `/api/v1/render/video/{job_id}` supporting HTTP Range headers (`206 Partial Content`) for seeking.

### 4.7 Multi-Tenant Workspaces & Enterprise RBAC
- **Organization Hierarchy:**
  - `Organization` $\rightarrow$ `Workspace` $\rightarrow$ `Project`
- **Role-Based Access Control (RBAC):**
  - `owner`: Full organizational control, billing, member deletion, organization transfer.
  - `admin`: Member invitations, workspace management, project administration.
  - `editor`: Creation and modification of projects, scenes, and characters.
  - `viewer`: Read-only access to workspaces and renders.

### 4.8 Authentication, Guest Mode & Session Hardening
- **User Authentication:**
  - Standard email/password registration with bcrypt password hashing.
  - JWT Access Tokens (15-minute lifetime).
  - Refresh Tokens stored with cryptographic hashes, device information, and family IDs for automatic reuse detection.
- **Session-Isolated Guest Mode:**
  - Instant access without upfront sign-up.
  - Guest users receive a deterministic guest token mapped to the seeded guest user record (`595744ab-c375-4bec-a3c0-429113163fe1`).
  - Row-level guest isolation cookies ensure that guest users cannot view or mutate other guest sessions' projects.
- **Inactivity Timeout:**
  - Session security watcher prompts re-authentication after prolonged idle periods.

### 4.9 Security, SSRF Guard & IDOR Defense
- **SSRF-Guarded Image Proxy (`/api/v1/ai/image-proxy`):**
  - Hardened against Server-Side Request Forgery.
  - Strict domain allowlist (`pollinations.ai`, `unsplash.com`).
  - DNS resolution check: rejects any private (RFC 1918), loopback (`127.0.0.1`), link-local, multicast, or cloud metadata IP addresses (`169.254.169.254`).
  - Disables HTTP redirects (`follow_redirects=False`) to block open-redirect bypasses.
  - Injects permissive CORS headers (`Access-Control-Allow-Origin: *`) allowing client HTML5 Canvas exports without browser taint errors.
- **Insecure Direct Object Reference (IDOR) Protection:**
  - Every project, scene, character, render job, and video endpoint validates that `resource.user_id == current_user_id`.
  - Path traversal checks ensure video download requests cannot escape `storage/videos/`.
- **Rate Limiting:**
  - In-memory sliding-window rate limiters on AI generation, TTS, render dispatch, and image proxying.
- **Exception Sanitization:**
  - In production (`ENVIRONMENT=production`), unhandled internal errors return sanitized generic error messages, preventing stack trace or database credential leaks.

### 4.10 Observability, Metrics & Health Probing
- **Prometheus Metrics (`/metrics`):**
  - Tracks HTTP request count, latencies by endpoint, active render concurrency, and AI provider availability.
- **Health Probes:**
  - `/health/live`: Shallow liveness probe for container orchestrators.
  - `/health/ready`: Deep readiness probe checking PostgreSQL connectivity, Redis status, storage write permissions, and AI provider statuses.
  - `/health/stats`: Real-time queue depth, active render count, and disk storage consumption.
- **UptimeRobot Integration:**
  - Pinged every 14 minutes in production to prevent Render.com free tier cold starts.

---

## 5. Complete Repository Directory & File Structure

```
VIDEO CREATION/
├── .env                              # Environment configurations (root)
├── .env.example                      # Template for environment variables
├── .gitignore                        # Git exclusion rules
├── DEPLOYMENT.md                     # Production deployment instructions (Render/Railway/Vercel)
├── PROJECT_MASTER_DOCUMENTATION.md   # Complete project master documentation (This File)
├── README.md                         # Quick start and high-level summary
├── brain.md                          # Single source of truth / agent memory
├── docker-compose.yml                # Multi-container orchestration (App + Redis + DB)
├── neon_schema.sql                   # Full PostgreSQL schema definition with 28 tables
├── start.bat                         # Windows one-click local developer boot script
│
├── backend/                          # FastAPI Backend Application
│   ├── .env                          # Backend local environment configuration
│   ├── .env.example                  # Backend environment template
│   ├── Dockerfile                    # Production Docker container build file
│   ├── alembic.ini                   # Alembic database migration config
│   ├── pytest.ini                    # Pytest configuration
│   ├── railway.json                  # Railway deployment configuration
│   ├── requirements.txt              # Python production dependencies
│   │
│   ├── alembic/                      # Database migrations
│   │   ├── env.py
│   │   └── script.py.mako
│   │
│   ├── app/                          # Core backend package
│   │   ├── main.py                   # FastAPI initialization, middlewares, health endpoints
│   │   │
│   │   ├── api/                      # Routing layer
│   │   │   └── v1/
│   │   │       ├── router.py         # Consolidates all v1 endpoint routers
│   │   │       └── endpoints/
│   │   │           ├── ai.py         # AI pipeline, TTS, word timings, image proxy, scene regen
│   │   │           ├── auth.py       # Login, register, token refresh, logout, password reset
│   │   │           ├── characters.py # CME CRUD, locking, script character extraction
│   │   │           ├── projects.py   # Project CRUD, style/language settings
│   │   │           ├── render.py     # Render job trigger, status polling, MP4 video download
│   │   │           ├── scenes.py     # Scene CRUD, reordering, narration & duration edits
│   │   │           ├── settings.py   # User preferences, themes, export defaults
│   │   │           ├── storage.py    # Media and asset retrieval
│   │   │           └── workspaces.py # Organizations, multi-tenant workspaces, RBAC members
│   │   │
│   │   ├── core/                     # Application infrastructure & utilities
│   │   │   ├── config.py             # Pydantic BaseSettings configuration
│   │   │   ├── dependencies.py       # FastAPI dependency injection (DB, Auth, Current User)
│   │   │   ├── metrics.py            # Prometheus metrics collection
│   │   │   ├── profiler.py           # Request performance profiling middleware
│   │   │   ├── rate_limit.py         # Sliding window rate limiting helpers
│   │   │   └── security.py           # Password hashing (bcrypt) and JWT decoding
│   │   │
│   │   ├── db/                       # Database engine & session
│   │   │   ├── base.py               # Declarative SQLAlchemy base
│   │   │   └── session.py            # Async engine and AsyncSessionLocal
│   │   │
│   │   ├── models/                   # SQLAlchemy declarative ORM models
│   │   │   ├── character.py          # CME models (Character, DNA, Styles, Outfits, Versions)
│   │   │   └── models.py             # User, Project, Script, Scene, RenderJob, Video, Org
│   │   │
│   │   ├── repositories/             # Data access repository layer
│   │   │   ├── project_repo.py
│   │   │   ├── render_repo.py
│   │   │   ├── scene_repo.py
│   │   │   ├── user_repo.py
│   │   │   └── video_job_repo.py
│   │   │
│   │   ├── schemas/                  # Pydantic request/response schemas
│   │   │   ├── auth.py               # Token responses, login requests
│   │   │   ├── character.py          # Character DNA, create/update schemas
│   │   │   ├── project.py            # Project create, update, responses
│   │   │   ├── render.py             # Render job response schemas
│   │   │   ├── scene.py              # Scene create, update, responses
│   │   │   ├── script.py             # Script parse schemas
│   │   │   └── user.py               # User registration, profile schemas
│   │   │
│   │   ├── services/                 # Business logic services
│   │   │   ├── ai_pipeline_service.py # Orchestrates script -> scenes -> images -> audio
│   │   │   ├── auth_service.py       # Authentication, refresh token rotation, guest logic
│   │   │   ├── project_service.py    # Project creation and scene lifecycle
│   │   │   ├── render_engine.py      # Native server-side FFmpeg compilation engine
│   │   │   ├── render_service.py     # Concurrency tracking, background task dispatch
│   │   │   ├── storage_service.py    # Local disk / Cloudflare R2 file management
│   │   │   ├── usage_service.py      # User quota and daily usage tracking
│   │   │   │
│   │   │   └── ai/                   # AI sub-services
│   │   │       ├── character_cache.py    # Fast in-memory CME lookup
│   │   │       ├── character_detector.py # Extracts named characters from script
│   │   │       ├── character_evaluator.py# Scores scene prompt consistency against DNA
│   │   │       ├── character_memory.py   # CME database management service
│   │   │       ├── fal_video_service.py  # Text-to-video AI generation via Fal.ai
│   │   │       ├── groq_key_manager.py   # 5-key Groq pool rotation and rate-limit handling
│   │   │       ├── image_generator.py    # Pollinations Flux, Replicate PuLID, DALL-E 3
│   │   │       ├── prompt_builder.py     # Prompt assembly with CME DNA injection
│   │   │       ├── script_analyzer.py    # Pacing, fidelity checking, scene segmentation
│   │   │       ├── subtitle_generator.py # Word-by-word timing calculation
│   │   │       ├── voice_generator.py    # Edge-TTS Indian voice synthesis
│   │   │       └── providers/            # Multi-provider video generation abstraction
│   │   │           ├── base.py
│   │   │           ├── fal_provider.py
│   │   │           ├── fallback_provider.py
│   │   │           └── provider_manager.py
│   │   │
│   │   ├── tasks/                    # Background execution
│   │   │   └── celery_app.py         # Celery task configuration
│   │   │
│   │   └── utils/                    # Shared backend helpers
│   │
│   ├── storage/                      # Local video and asset persistence
│   │   └── videos/                   # Rendered MP4 files
│   │
│   └── tests/                        # Comprehensive test suite
│       ├── test_api.py               # Auth, project, and health endpoint tests
│       ├── test_render_pipeline.py   # Real FFmpeg MP4 generation & ffprobe validation
│       └── test_security.py          # IDOR, Guest isolation, SSRF proxy blocks
│
└── frontend/                         # Next.js 14 Frontend Application
    ├── .env.local.example            # Frontend environment template
    ├── next.config.js                # Next.js build and proxy configuration
    ├── package.json                  # NPM dependencies and scripts
    ├── postcss.config.js             # PostCSS plugins
    ├── tailwind.config.ts            # Tailwind styling tokens and animations
    ├── tsconfig.json                 # TypeScript compiler options
    ├── vercel.json                   # Vercel deployment routing and headers
    │
    ├── app/                          # Next.js App Router
    │   ├── globals.css               # Global CSS, typography, theme colors
    │   ├── layout.tsx                # Root layout with font injection
    │   │
    │   ├── (auth)/                   # Authentication route group
    │   │   ├── layout.tsx            # Clean centered auth layout
    │   │   ├── login/page.tsx        # Login page
    │   │   ├── register/page.tsx     # Registration page
    │   │   └── forgot-password/page.tsx # Password recovery
    │   │
    │   ├── (dashboard)/              # Authenticated studio workspace
    │   │   ├── layout.tsx            # Studio shell with Sidebar and Navbar
    │   │   ├── characters/page.tsx   # CME Character Studio (create, lock, inspect DNA)
    │   │   ├── dashboard/page.tsx    # Recent projects, creation cards, quick actions
    │   │   ├── settings/page.tsx     # User preferences, themes, export quality
    │   │   └── projects/
    │   │       ├── page.tsx          # Project gallery with filtering and pagination
    │   │       ├── new/page.tsx      # New project creation & script input wizard
    │   │       └── [id]/
    │   │           └── editor/page.tsx # Full Studio Editor (Player, Inspector, Timeline)
    │   │
    │   └── (public)/                 # Landing Page
    │       └── page.tsx              # High-conversion marketing page
    │
    ├── components/                   # React components
    │   ├── auth/                     # AuthSessionWatcher, LoginForm, RegisterForm
    │   ├── character/                # CharacterCard, CharacterDNAInspector, CreateCharacterModal
    │   ├── editor/                   # VideoPreview, SceneEditor, Timeline, ToolBar, RenderModal
    │   ├── project/                  # StyleSelector, VoiceSelector
    │   └── shared/                   # Navbar, Sidebar, MobileNav, Logo
    │
    └── lib/                          # Client libraries & utilities
        ├── api/                      # Axios API clients (auth, projects, scenes, ai, render, characters)
        ├── auth/                     # Token storage, guest token resolution, session headers
        ├── hooks/                    # Custom React hooks
        ├── stores/                   # Zustand stores (editorStore, userStore)
        └── utils/                    # Formatting, duration calculations, styling helpers
```

---

## 6. Database Schema & Data Model Specification

The database uses Neon PostgreSQL with 28 relational tables ensuring strict referential integrity.

### Primary Database Tables
```
 1. users                        (id, email, full_name, avatar_url, auth_provider, is_active, is_verified)
 2. refresh_tokens               (token_hash, user_id, family_id, is_revoked, device_info, expires_at)
 3. organizations                (id, name, slug, owner_id)
 4. workspaces                   (id, organization_id, name, is_default)
 5. organization_members         (id, organization_id, user_id, role)
 6. projects                     (id, user_id, workspace_id, title, description, style, language, status)
 7. scripts                      (id, project_id, content, word_count, estimated_duration, status, analysis_result)
 8. scenes                       (id, project_id, script_id, scene_number, duration, narration, subtitle, image_prompt, animation_style, transition, camera_motion)
 9. scene_assets                 (id, scene_id, asset_type, url, storage_path, metadata)
10. render_jobs                  (id, project_id, user_id, status, progress, celery_task_id, error_message, retry_count)
11. videos                       (id, project_id, render_job_id, url, storage_path, duration, width, height, file_size, format)
12. images                       (id, project_id, scene_id, url, storage_path, prompt, style, provider)
13. audio                        (id, project_id, scene_id, audio_type, url, storage_path, duration)
14. user_settings                (id, user_id, theme, language, notifications_enabled, export_defaults, video_quality)
15. user_usage                   (id, user_id, ai_requests_today, video_generations_today, render_jobs_today, rendered_seconds_total)
16. exports                      (id, video_id, user_id, format, quality, url, expires_at, download_count)
17. video_generation_jobs        (id, scene_id, project_id, user_id, provider, prompt, status, video_url)
18. characters                   (id, user_id, project_id, character_code, name, is_locked, is_favorite, consistency_score)
19. character_profiles           (id, character_id, role, age, gender, ethnicity, summary)
20. character_dna                (id, character_id, skin_tone, hair_color, hair_style, eye_color, face_shape, outfit, shoes, visual_style, prompt_prefix, prompt_suffix, negative_prompt)
21. character_embeddings         (id, character_id, embedding_vector, model_version)
22. character_styles             (id, character_id, style_name, rendering_engine, style_prompt_modifiers)
23. character_outfits            (id, character_id, outfit_name, top_clothing, bottom_clothing, footwear, color_palette)
24. character_accessories        (id, character_id, accessory_type, item_description)
25. character_relationships      (id, character_id, related_character_id, relationship_type, notes)
26. character_reference_images   (id, character_id, image_url, extracted_metadata, is_primary)
27. character_scene_assignments  (id, character_id, scene_id)
28. character_versions           (id, character_id, version_number, dna_snapshot)
```

---

## 7. REST API Endpoint & Contract Specification

All endpoints are prefixed with `/api/v1` (with the exception of `/metrics` and `/health/*` at root).

### 7.1 Authentication & Profile (`/api/v1/auth`)
| Method | Path | Description | Access |
|---|---|---|---|
| `POST` | `/auth/register` | Register new user with email and password | Public |
| `POST` | `/auth/login` | Authenticate user and receive access + refresh token | Public |
| `GET` | `/auth/me` | Fetch authenticated user profile | Authenticated / Guest |
| `POST` | `/auth/refresh` | Rotate refresh token and obtain fresh access token | Public |
| `POST` | `/auth/logout` | Revoke active refresh token family and logout | Authenticated |
| `POST` | `/auth/forgot-password` | Initiate password recovery workflow | Public |

### 7.2 Projects (`/api/v1/projects`)
| Method | Path | Description | Access |
|---|---|---|---|
| `GET` | `/projects` | List projects belonging to current user (supports pagination) | Authenticated / Guest |
| `POST` | `/projects` | Create a new project with optional script content | Authenticated / Guest |
| `GET` | `/projects/{project_id}` | Retrieve complete project details including scenes & script | Authenticated / Guest |
| `PUT` | `/projects/{project_id}` | Update title, style, or language | Authenticated / Guest |
| `DELETE` | `/projects/{project_id}` | Permanently delete project and cascade all scenes/assets | Authenticated / Guest |

### 7.3 Scenes (`/api/v1/scenes`)
| Method | Path | Description | Access |
|---|---|---|---|
| `GET` | `/scenes/project/{project_id}` | Fetch ordered list of scenes for a project | Authenticated / Guest |
| `PUT` | `/scenes/{scene_id}` | Update narration, prompt, camera motion, duration | Authenticated / Guest |
| `POST` | `/scenes/reorder` | Update ordering sequence of scenes | Authenticated / Guest |
| `DELETE` | `/scenes/{scene_id}` | Delete a scene and adjust indices | Authenticated / Guest |

### 7.4 AI Pipeline & Media Generation (`/api/v1/ai`)
| Method | Path | Description | Access |
|---|---|---|---|
| `POST` | `/ai/generate-pipeline/{project_id}` | End-to-end generation: script $\rightarrow$ scenes $\rightarrow$ assets | Authenticated / Guest |
| `POST` | `/ai/generate-scenes` | Generates scenes from raw text without modifying DB | Authenticated / Guest |
| `POST` | `/ai/tts` | Synthesizes speech from text; returns MP3 binary | Authenticated / Guest |
| `GET` | `/ai/tts` | Streaming audio endpoint for HTML5 `<audio>` tags | Authenticated / Guest |
| `POST` | `/ai/word-timings` | Calculates per-word start/end timing arrays | Authenticated / Guest |
| `GET` | `/ai/image-proxy` | SSRF-safe proxy for client canvas video export | Authenticated / Guest |
| `POST` | `/ai/regenerate-scene-image` | Re-runs visual generation for a single scene | Authenticated / Guest |
| `POST` | `/ai/generate-scene-prompt` | Generates high-detail visual prompt for scene text | Authenticated / Guest |
| `POST` | `/ai/generate-scene-video` | Triggers Fal.ai text-to-video for dynamic scene | Authenticated / Guest |
| `GET` | `/ai/voices` | Returns catalog of available Indian Neural voices | Authenticated / Guest |
| `GET` | `/ai/styles` | Returns supported artistic styles | Authenticated / Guest |
| `GET` | `/ai/groq-status` | Health & quota status of Groq 5-key pool | Authenticated / Guest |

### 7.5 Character Memory Engine (`/api/v1/characters`)
| Method | Path | Description | Access |
|---|---|---|---|
| `POST` | `/characters` | Create a new character with DNA parameters | Authenticated / Guest |
| `GET` | `/characters` | List all characters belonging to user | Authenticated / Guest |
| `GET` | `/characters/{character_id}` | Fetch specific character profile & DNA | Authenticated / Guest |
| `POST` | `/characters/{character_id}/lock` | Lock character DNA to freeze identity | Authenticated / Guest |
| `POST` | `/characters/{character_id}/unlock` | Unlock character DNA for modifications | Authenticated / Guest |
| `POST` | `/characters/extract` | Auto-detect character names and roles from script | Authenticated / Guest |
| `POST` | `/characters/evaluate` | Score scene prompt consistency against DNA | Authenticated / Guest |

### 7.6 Video Render Pipeline (`/api/v1/render`)
| Method | Path | Description | Access |
|---|---|---|---|
| `POST` | `/render/start/{project_id}` | Dispatches background server-side FFmpeg compilation | Authenticated / Guest |
| `GET` | `/render/status/{job_id}` | Polls render job progress (0–100%) and status | Authenticated / Guest |
| `POST` | `/render/cancel/{job_id}` | Cancels an ongoing render job | Authenticated / Guest |
| `GET` | `/render/video/{job_id}` | Streams completed MP4 with HTTP Range support | Authenticated / Guest |

### 7.7 Workspaces & Enterprise RBAC (`/api/v1/workspaces`)
| Method | Path | Description | Access |
|---|---|---|---|
| `POST` | `/workspaces/organizations` | Create a new multi-user organization | Authenticated |
| `GET` | `/workspaces/organizations` | List organizations user belongs to | Authenticated |
| `POST` | `/workspaces` | Create a workspace under an organization | Authenticated |
| `GET` | `/workspaces` | List accessible workspaces | Authenticated |
| `POST` | `/workspaces/organizations/{org_id}/members` | Invite new member with role (owner, admin, editor, viewer) | Authenticated (Admin+) |
| `DELETE` | `/workspaces/organizations/{org_id}/members/{user_id}` | Remove member from organization | Authenticated (Admin+) |

---

## 8. Frontend State Management & Component Hierarchy

### Zustand Store (`editorStore.ts`)
The entire interactive studio is managed via a centralized Zustand store:
- `project: Project | null`: Active project metadata, style, title, language.
- `scenes: Scene[]`: Array of scene objects in sequential playback order.
- `activeSceneId: string | null`: Currently selected scene in timeline/inspector.
- `currentTime: number`: Global playback scrubber position in seconds.
- `isPlaying: boolean`: State of canvas video playback loop.
- `totalDuration: number`: Computed sum of all scene durations.
- `activeAudioElement: HTMLAudioElement | null`: Direct reference to synthesized narration audio.

### Studio Component Hierarchy
```
EditorPage (/projects/[id]/editor)
├── ToolBar
│   ├── Project Title & Style Badge
│   ├── AI Scene Generation Trigger
│   └── Export & Render Modal Trigger
│
├── Workspace Viewport
│   ├── VideoPreview (Center)
│   │   ├── Smartphone Frame (9:16 vertical ratio)
│   │   ├── Dynamic Media Layer (<canvas> / <img> / <video>)
│   │   ├── Animated Pan/Zoom Ken Burns Transformer
│   │   ├── Word-by-Word Karaoke Subtitle Overlay
│   │   └── Floating Transport Controls (Play, Pause, Restart, Seek)
│   │
│   └── SceneEditor (Right Panel / Inspector)
│       ├── Scene Header & Order Identifier
│       ├── Narration Input (User's Script Slice)
│       ├── Visual Image Prompt & Regenerate Button
│       ├── Camera Motion Selector (Push, Pull, Pan Left, Pan Right)
│       ├── Animation Style & Transition Selectors
│       └── Duration Slider (3.0s – 10.0s)
│
├── Timeline (Bottom Dock)
│   ├── Time Indicator & Playhead Scrubber
│   ├── Scene Strip Cards with Thumbnails & Durations
│   └── Add Scene / Reorder Controls
│
└── RenderModal (Popup Dialog)
    ├── Resolution Picker (1080x1920 Full HD / 720x1280 HD)
    ├── Server FFmpeg Render Status & Progress Bar
    ├── Live Streaming Video Preview Player
    └── Direct MP4 Download Button
```

---

## 9. Deployment, Infrastructure & Operations Guide

### Production Deployment Topology
| Component | Platform | URL / Host |
|---|---|---|
| **Frontend** | Vercel | `https://akm-motion.vercel.app` |
| **Backend API** | Render | `https://akmmotion-backend.onrender.com` |
| **Database** | Neon Serverless PostgreSQL | `ep-wispy-waterfall-ay9ni5ea-pooler.c-5.us-east-2.aws.neon.tech` |
| **Liveness Poller**| UptimeRobot | Pings `/api/v1/health` every 14 minutes |

### Persistent Storage Requirement
When deploying the backend container to cloud platforms (Render, Railway, Fly.io):
- Rendered MP4 files are written to `/app/storage/videos/{job_id}.mp4`.
- A persistent volume must be mounted at `/app/storage` with `STORAGE_DIR=/app/storage` to prevent videos from being erased during container restarts.

### Docker Container Specification
```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 10. Configuration & Environment Variables Reference

| Variable | Type | Default | Description |
|---|---|---|---|
| `ENVIRONMENT` | string | `development` | `development` or `production` (enforces HSTS and secure cookies) |
| `DEBUG` | boolean | `True` | Enables debug logging and interactive error pages |
| `DATABASE_URL` | string | Neon pooler URI | Asynchronous PostgreSQL connection string (`postgresql+asyncpg://...`) |
| `SYNC_DATABASE_URL` | string | Neon pooler URI | Synchronous PostgreSQL connection string (`postgresql://...`) |
| `JWT_SECRET` | string | secret | Cryptographic secret for signing JWT access and refresh tokens |
| `JWT_ACCESS_EXPIRE_MINUTES` | int | `15` | Access token lifespan in minutes |
| `JWT_REFRESH_EXPIRE_DAYS` | int | `7` | Refresh token lifespan in days |
| `GROQ_API_KEY` | string | `""` | Primary Groq API key for Llama 3 scene generation |
| `GROQ_API_KEY_2` to `_5` | string | `""` | Secondary failover keys for round-robin rotation |
| `OPENAI_API_KEY` | string | `""` | Optional fallback for GPT-3.5 and DALL-E 3 |
| `REPLICATE_API_TOKEN` | string | `""` | Optional token for PuLID FaceID visual consistency |
| `FAL_KEY` | string | `""` | Optional API key for Fal.ai Kling text-to-video generation |
| `STORAGE_DIR` | string | `""` | Path to persistent volume storage directory |
| `FFMPEG_PATH` | string | `ffmpeg` | Path or command for FFmpeg executable |
| `MAX_CONCURRENT_RENDERS_GLOBAL` | int | `5` | Maximum simultaneous FFmpeg render processes |
| `MAX_CONCURRENT_RENDERS_PER_USER` | int | `1` | Maximum simultaneous renders allowed per user |
| `FRONTEND_URL` | string | `http://localhost:3000` | Allowed CORS frontend URL |
| `BACKEND_URL` | string | `http://localhost:8000` | Public backend host URL |

---

## 11. Testing, Quality Assurance & Verification Metrics

The codebase maintains strict quality thresholds with automated regression testing:

### Backend Test Coverage (26/26 Tests Passing)
- **`tests/test_security.py` (15/15 Passed):**
  - Guest isolation: verifies session cookies cannot read foreign projects.
  - IDOR ownership validation: ensures users cannot delete or update another user's scenes or renders.
  - SSRF protection: validates that private IP addresses (`127.0.0.1`, `10.0.0.0/8`, `192.168.0.0/16`) and unauthorized domains are rejected by the image proxy.
  - Rate limiting verification: checks rejection after burst limits.
- **`tests/test_api.py` (6/6 Passed):**
  - User registration, login, JWT validation, project creation, scene query, and health check validation.
- **`tests/test_render_pipeline.py` (5/5 Passed):**
  - Real server FFmpeg video compilation.
  - Multi-scene ffprobe validation checking 1080×1920 resolution, H.264 video codec, AAC audio codec, and duration accuracy.
  - Error recovery, concurrency limits, and stale render job cleanups.

### Frontend Verification
- TypeScript verification: `npx tsc --noEmit` $\rightarrow$ **0 errors**.
- Next.js production build: `npm run build` $\rightarrow$ **12 static and dynamic routes compiled cleanly**.

---
*End of AkmMotion Master Documentation — Generated 2026-10-04*
