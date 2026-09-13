# 🎬 AkmMotion — AI Script-to-YouTube Shorts SaaS Platform
> **Complete Production Architecture & System Documentation**

---

## 📌 Executive Summary

**AkmMotion** is an enterprise-grade AI SaaS platform designed to transform raw scripts and text topics into high-retention, professional 9:16 vertical videos (YouTube Shorts, Instagram Reels, TikTok) in under 2 minutes.

Built on Next.js 14, FastAPI, Neon PostgreSQL, and Web Audio/Canvas rendering pipelines, AkmMotion operates **100% free of paid API key dependencies**, relying on robust open AI engines (Pollinations AI, gTTS, Unsplash, Web Speech API, and rule-based NLP).

---

## 🚀 Key Selling Points & Core Capabilities

| Feature | Description |
|---|---|
| 🧬 **Character Memory Engine (CME)** | **Persistent AI visual memory & character identity locking** ensuring 100% visual consistency (same face, hair, skin, outfit, style) across all generated video scenes. |
| 🧠 **AI Script Intelligence Engine** | Analyzes scripts for quality, calculates a **0–100 Script Health Score**, and provides 1-click safe AI auto-improvement with side-by-side diff comparison. |
| 🎙️ **Native Multi-Language Voiceover** | Auto-detects English (`en-IN` Indian English Accent) and Hindi (`hi-IN` Native Indian Hindi Voice) using backend `gTTS`. |
| 📸 **Pollinations AI + Unsplash Visuals** | Generates 100% topic-matched 1080x1920 vertical visual images for all scenes with fail-safe fallback handlers. |
| 🎞️ **Interactive Studio Editor & CME Studio** | Full timeline control, real-time video player with Ken Burns motion, subtitle caption editor, and Character Memory Studio (`/characters`). |
| 🎬 **Client-Side Video & Audio Exporter** | Encodes 540x960 / 1080x1920 vertical video frames + voice narration into a downloadable MP4/WebM file inside a compact 9:16 smartphone preview frame. |
| 🗄️ **Neon Serverless PostgreSQL DB** | Persists users, projects, scripts, scenes, scene assets, 11 CME tables, and render jobs. |

---

## 🧜‍♂️ CHARACTER MEMORY ENGINE (CME) ARCHITECTURE

```
+-----------------------------------------------------------------------------------+
|                           CHARACTER MEMORY ENGINE (CME)                            |
+-----------------------------------------------------------------------------------+
| 1. Character Detector Service (NLP Named Entity & Role Extraction)                |
| 2. 11 Database Tables (Characters, Profiles, DNA, Embeddings, Styles, Outfits...) |
| 3. Character Memory Service + <100ms In-Memory CharacterCache                     |
| 4. Character DNA Prompt Injector (Locked Prompt Prefixes & Suffixes)              |
| 5. Character Consistency Evaluator (0-100 Match Rating & Drift Warnings)          |
| 6. Character Studio UI (/characters Dashboard & CharacterDNAInspector Modal)      |
+-----------------------------------------------------------------------------------+
```

### CME 11 Database Tables (Neon PostgreSQL)
1. `characters` — Main character identity and lock state (`is_locked`).
2. `character_profiles` — Backstory, role, age, gender, summary.
3. `character_dna` — Locked visual traits (hair, skin, eyes, outfit, shoes, visual style, camera/lighting).
4. `character_embeddings` — Visual feature vectors for facial identity recognition.
5. `character_styles` — Art style presets (Pixar 3D Render, Anime, Realistic, Comic).
6. `character_outfits` — Preset clothing items and color palettes.
7. `character_accessories` — Glasses, watches, hats, jewelry.
8. `character_relationships` — Story connections (Father, Friend, Sibling, Pet).
9. `character_reference_images` — Reference image uploads and extracted feature metadata.
10. `character_scene_assignments` — Scene appearances and pose/emotion states.
11. `character_versions` — Audit history snapshots (V1, V2, V3) for full rollback capability.

---

## 🏗️ System Architecture

```
                                  +------------------------------------+
                                  |         Next.js 14 Frontend        |
                                  |     (App Router, Zustand, Canvas)  |
                                  +-----------------+------------------+
                                                    |
                                       REST APIs (HTTP / JSON)
                                                    |
                                  +-----------------v------------------+
                                  |           FastAPI Backend          |
                                  |    (Uvicorn, Async SQLAlchemy 2.0) |
                                  +--------+-----------------+---------+
                                           |                 |
                       +-------------------+                 +-------------------+
                       |                                                         |
         +-------------v-------------+                             +-------------v-------------+
         |    Neon Serverless DB     |                             |       AI Sub-Services     |
         |    (PostgreSQL Cloud)     |                             |  • Character Memory Engine|
         +---------------------------+                             |  • Script Intelligence    |
                                                                   |  • Pollinations AI Images |
                                                                   |  • Native gTTS Voiceover  |
                                                                   +---------------------------+
```