import io
import re
import asyncio
import urllib.parse
import hashlib
from uuid import UUID
from functools import partial
from fastapi import APIRouter, Depends, Body, Response, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_db, get_current_user_id
from app.schemas.project import ProjectResponse
from app.services.ai_pipeline_service import AIPipelineService
from app.services.ai.script_intelligence import ScriptHealthEvaluator, ScriptImprover
from app.services.ai.subtitle_generator import SubtitleGeneratorService
from app.services.ai.voice_generator import VoiceGeneratorService

router = APIRouter(prefix="/ai", tags=["AI Pipeline"])


# ─────────────────────────────────────────────────────────────────────────────
# Script Intelligence
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/analyze-script")
async def analyze_script_health(payload: dict = Body(...)):
    """Evaluates script health and returns 0-100 score + AI suggestions."""
    script_text = payload.get("script", "")
    language = payload.get("language", "Auto Detect")
    report = ScriptHealthEvaluator.evaluate(script_text, language)
    return report


@router.post("/improve-script")
async def auto_improve_script(payload: dict = Body(...)):
    """Auto-improves script grammar, flow, and hook while preserving meaning."""
    script_text = payload.get("script", "")
    result = ScriptImprover.improve(script_text)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# AI Pipeline
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/generate-pipeline/{project_id}", response_model=ProjectResponse)
async def generate_ai_pipeline(
    project_id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Runs the full AI pipeline: script → scenes → images → audio → subtitles."""
    service = AIPipelineService(db)
    project = await service.run_pipeline(project_id, UUID(current_user_id))
    return ProjectResponse.model_validate(project)


# ─────────────────────────────────────────────────────────────────────────────
# TTS — Indian Accent Voice Synthesis
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/tts")
async def generate_speech(payload: dict = Body(...)):
    """
    Synthesizes Indian-accent speech (gTTS) for a given text.
    Accepts: { text, language?, gender? }
    Returns: MP3 audio bytes (audio/mpeg).
    """
    raw_text = payload.get("text", "").strip()
    language = payload.get("language", "en")  # 'en' or 'hi'
    gender   = payload.get("gender", "male")  # 'male' or 'female'

    # Clean text: keep letters, digits, spaces, punctuation and Devanagari
    text = re.sub(r"[^\w\s.,?!'\-\u0900-\u097F]", "", raw_text).strip()

    if not text:
        return Response(status_code=400, content=b"Text required")

    # Auto-detect Hindi
    if language == "en" and re.search(r"[\u0900-\u097F]", text):
        language = "hi"

    try:
        voice_svc = VoiceGeneratorService()
        # Run blocking gTTS network call in a thread pool (non-blocking for event loop)
        loop = asyncio.get_event_loop()
        audio_bytes = await loop.run_in_executor(
            None,
            partial(voice_svc.synthesize_to_bytes, text, language, gender)
        )

        if not audio_bytes:
            # Return minimal silent MP3 instead of 500 so render doesn't break
            return Response(
                content=_silent_mp3(),
                media_type="audio/mpeg",
                headers={"X-TTS-Fallback": "silent"}
            )

        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={"Content-Length": str(len(audio_bytes))}
        )
    except Exception as e:
        print(f"[TTS Endpoint] Error: {e}")
        import traceback; traceback.print_exc()
        # Never return 500 to the render engine — silent fallback keeps video rendering
        return Response(
            content=_silent_mp3(),
            media_type="audio/mpeg",
            headers={"X-TTS-Error": str(e)[:120]}
        )


def _silent_mp3() -> bytes:
    """Returns a minimal valid 0.5s silent MP3 frame so AudioContext.decodeAudioData doesn't fail."""
    try:
        from gtts import gTTS
        tts = gTTS(" ", lang="en")
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return buf.read()
    except Exception:
        # 128-byte silent MP3 header (ID3v2 minimal frame)
        return bytes([
            0xFF,0xFB,0x90,0x00, 0x00,0x00,0x00,0x00,
            0x00,0x00,0x00,0x00, 0x00,0x00,0x00,0x00,
        ] * 32)


# ─────────────────────────────────────────────────────────────────────────────
# Word-Level Subtitle Timings
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/word-timings")
async def get_word_timings(payload: dict = Body(...)):
    """
    Returns per-word timing array for karaoke subtitle sync.
    Accepts: { text, duration }
    Returns: [{ word, start, end, index }, ...]
    """
    text = payload.get("text", "").strip()
    duration = float(payload.get("duration", 6.0))

    if not text:
        return []

    from app.services.ai.subtitle_generator import SubtitleGeneratorService
    timings = SubtitleGeneratorService.compute_word_timings_from_text(text, duration)
    return timings


# ─────────────────────────────────────────────────────────────────────────────
# Image Proxy — Fixes Pollinations/Unsplash 403 canvas taint in RenderModal
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/image-proxy")
async def image_proxy(url: str):
    """
    Server-side image proxy that fetches external images and returns them
    with CORS headers, bypassing browser canvas taint restrictions.
    Used by RenderModal.tsx to load images into <canvas> for video export.
    """
    import httpx
    if not url or not url.startswith("http"):
        return Response(status_code=400, content=b"Invalid URL")

    # Allow only known safe image hosts
    allowed_hosts = [
        "image.pollinations.ai",
        "images.unsplash.com",
        "pollinations.ai",
        "source.unsplash.com",
    ]
    parsed = urllib.parse.urlparse(url)
    if not any(parsed.netloc.endswith(h) for h in allowed_hosts):
        return Response(status_code=403, content=b"Host not allowed")

    try:
        async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept":     "image/webp,image/png,image/jpeg,*/*",
            }
            resp = await client.get(url, headers=headers)
            content_type = resp.headers.get("content-type", "image/jpeg")
            content = resp.content
            if not content or len(content) == 0:
                # If upstream returned empty, return fallback 1x1 transparent JPEG/PNG
                content = _minimal_jpeg()
            return Response(
                content=content,
                media_type=content_type,
                headers={
                    "Access-Control-Allow-Origin":  "*",
                    "Access-Control-Allow-Methods": "GET, OPTIONS",
                    "Access-Control-Allow-Headers": "*",
                    "Cache-Control":                "public, max-age=3600",
                    "X-Proxy-Source":               parsed.netloc,
                }
            )
    except Exception as e:
        print(f"[ImageProxy] Error fetching {url[:80]}: {e}")
        # Return fallback image instead of 502 to avoid canvas breakage
        return Response(
            content=_minimal_jpeg(),
            media_type="image/jpeg",
            headers={"Access-Control-Allow-Origin": "*", "X-Proxy-Fallback": "1"}
        )


def _minimal_jpeg() -> bytes:
    """Minimal valid 1x1 black JPEG frame."""
    return bytes([
        0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01, 0x01, 0x01, 0x00, 0x48,
        0x00, 0x48, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43, 0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08,
        0x07, 0x07, 0x07, 0x09, 0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
        0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20, 0x24, 0x2E, 0x27, 0x20,
        0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29, 0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27,
        0x39, 0x3D, 0x38, 0x32, 0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
        0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x1F, 0x00, 0x00, 0x01, 0x05, 0x01, 0x01,
        0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04,
        0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01, 0x00, 0x00, 0x3F,
        0x00, 0xBF, 0x80, 0xFF, 0xD9
    ])


# ─────────────────────────────────────────────────────────────────────────────
# Per-Scene Image Regeneration
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/regenerate-scene-image")
async def regenerate_scene_image(
    payload: dict = Body(...),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Regenerates the image for a single scene with a fresh Pollinations seed.
    Accepts: { scene_id, prompt?, style? }
    Returns: { scene_id, image_url }
    """
    from app.models.models import Scene, SceneAsset, AssetType

    scene_id_str = payload.get("scene_id", "")
    custom_prompt = payload.get("prompt", "")
    style = payload.get("style", "Explainer")

    if not scene_id_str:
        return Response(status_code=400, content=b"scene_id required")

    try:
        scene_id = UUID(scene_id_str)
    except ValueError:
        return Response(status_code=400, content=b"Invalid scene_id")

    # Fetch scene from DB
    result = await db.execute(
        select(Scene)
        .where(Scene.id == scene_id)
        .options(selectinload(Scene.assets))
    )
    scene = result.scalar_one_or_none()
    if not scene:
        return Response(status_code=404, content=b"Scene not found")

    # Build prompt — use custom or existing scene prompt
    base_prompt = custom_prompt or scene.image_prompt or "cinematic scene"
    clean_prompt = re.sub(r'[*#]', '', base_prompt).strip()
    clean_prompt = re.sub(r'[^\x00-\x7F]+', ' ', clean_prompt)
    clean_prompt = re.sub(r'\s+', ' ', clean_prompt).strip()
    if not clean_prompt or len(clean_prompt) < 5:
        clean_prompt = f"dramatic cinematic scene capturing the emotional story moment, {style} visual style"

    # Style visual modifiers
    style_visual = {
        "Cinematic": "dramatic cinematic lighting, film grain, anamorphic lens, masterpiece",
        "Story":     "cinematic storytelling, golden hour lighting, emotional narrative atmosphere",
        "Vlog":      "warm natural daylight, lifestyle aesthetic, vibrant colors",
        "Anime":     "anime art style, vibrant colors, cel-shaded, manga panel",
        "Explainer": "clean bright lighting, professional corporate aesthetic",
        "Finance":   "clean corporate aesthetic, crisp architectural lighting",
    }.get(style, "cinematic lighting, ultra detailed")

    full_prompt = (
        f"{clean_prompt}, {style_visual}, "
        f"9:16 vertical format, cinematic composition, photorealistic 8k, no text overlays"
    )

    # Generate fresh seed (different from original)
    import time
    fresh_seed = int(hashlib.md5(f"{clean_prompt}{time.time()}".encode()).hexdigest(), 16) % 999999
    encoded = urllib.parse.quote(full_prompt)
    new_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&model=flux&nologo=true&seed={fresh_seed}"

    # Update or create image asset in DB
    image_asset = next((a for a in scene.assets if a.asset_type == AssetType.image), None)
    if image_asset:
        image_asset.url = new_url
        image_asset.metadata_json = {
            **(image_asset.metadata_json or {}),
            "regenerated": True,
            "prompt": full_prompt
        }
    else:
        new_asset = SceneAsset(
            scene_id=scene.id,
            asset_type=AssetType.image,
            url=new_url,
            storage_path=f"images/{scene.id}_regen.jpg",
            metadata_json={"regenerated": True, "prompt": full_prompt}
        )
        db.add(new_asset)

    # Also update scene.image_prompt in DB if custom prompt was provided
    if custom_prompt:
        scene.image_prompt = custom_prompt

    await db.commit()

    return {"scene_id": str(scene_id), "image_url": new_url, "prompt": full_prompt}


@router.post("/generate-scene-prompt")
async def generate_scene_prompt(
    payload: dict = Body(...),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Uses LLM to craft an accurate, vivid English visual prompt for a scene based on its narration and context.
    Accepts: { narration, style?, story_context? }
    Returns: { prompt }
    """
    narration = payload.get("narration", "").strip()
    style = payload.get("style", "Cinematic")
    context = payload.get("story_context", "")

    if not narration:
        return {"prompt": f"Cinematic wide establishing shot, {style} visual style, 9:16 vertical format, 8k"}

    try:
        from app.services.ai.groq_key_manager import GroqKeyManager
        groq = GroqKeyManager.get_instance()
        sys_msg = (
            "You are an expert AI image prompt engineer for cinematic vertical 9:16 videos. "
            "Write a single, highly detailed, evocative ENGLISH visual prompt describing what should be seen in the scene. "
            "Rules:\n"
            "1. Output ONLY the prompt string in English. No explanations, no prefixes, no quotes.\n"
            "2. Describe: shot type, camera angle, subject, cultural/historical setting, specific action, lighting, textures, mood.\n"
            "3. If the narration is in Hindi or another language, translate the visual meaning into an accurate visual depiction.\n"
            "4. NEVER include dialogue, text overlays, or non-English characters."
        )
        user_msg = f"Narration: {narration}\nVisual Style: {style}\nOverall Story Context: {context}"
        content = await groq.chat(
            messages=[
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": user_msg}
            ],
            temperature=0.7,
            max_tokens=250
        )
        clean = content.strip().strip('"').strip("'")
        return {"prompt": clean}
    except Exception as e:
        print(f"[generate-scene-prompt] LLM prompt gen error: {e}")
        return {"prompt": f"Cinematic shot, {style} style, dramatic lighting, 9:16 vertical format, 8k photorealistic"}


# ─────────────────────────────────────────────────────────────────────────────
# Voice & Style Listings
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/voices")
async def list_ai_voices():
    """Lists available voice options for the voice picker UI."""
    return [
        {"id": "en_male",  "name": "Rishi — Indian English",  "lang": "en", "gender": "male",   "provider": "gtts"},
        {"id": "en_female","name": "Heera — Indian English",   "lang": "en", "gender": "female", "provider": "gtts"},
        {"id": "hi_male",  "name": "Arjun — Hindi",            "lang": "hi", "gender": "male",   "provider": "gtts"},
        {"id": "hi_female","name": "Swara — Hindi",            "lang": "hi", "gender": "female", "provider": "gtts"},
    ]


@router.get("/styles")
async def list_video_styles():
    """Lists available visual style presets."""
    return [
        {"id": "Explainer", "name": "Explainer",    "description": "Clean, informative, bright"},
        {"id": "Cinematic",  "name": "Cinematic",    "description": "Dramatic film-quality look"},
        {"id": "Vlog",       "name": "Vlog",         "description": "Natural lifestyle feel"},
        {"id": "Anime",      "name": "Anime",        "description": "Vibrant anime art style"},
        {"id": "Story",      "name": "Storytelling", "description": "Emotional narrative mood"},
        {"id": "Finance",    "name": "Finance",      "description": "Professional, trust-building"},
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Groq Key Status (for monitoring/debugging)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/groq-status")
async def groq_key_status():
    """
    Returns health status of all configured Groq API keys.
    Shows which keys are available/cooling down without exposing actual key values.
    """
    try:
        from app.services.ai.groq_key_manager import GroqKeyManager
        manager = GroqKeyManager.get_instance()
        status  = manager.status()
        return {
            "total_keys": len(status),
            "available":  sum(1 for s in status if s["available"]),
            "model":      manager.BEST_MODEL,
            "keys":       status,
        }
    except Exception as e:
        return {"error": str(e), "total_keys": 0, "available": 0}


# ─────────────────────────────────────────────────────────────────────────────
# Direct Scene Generation (Groq LLM → scene array, no DB write)
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/generate-scenes")
async def generate_scenes_from_script(payload: dict = Body(...)):
    """
    Runs Groq scene analysis directly on a script and returns scene JSON.
    Accepts: { script, style?, language? }
    Returns: { scenes: [...], source: 'groq'|'openai'|'heuristic' }
    No authentication required — used during project creation flow.
    """
    from app.services.ai.script_analyzer import ScriptAnalyzerService
    script_text = payload.get("script", "").strip()
    style       = payload.get("style", "Explainer")
    language    = payload.get("language", "en")

    if not script_text:
        return Response(status_code=400, content=b"script field required")

    analyzer = ScriptAnalyzerService()

    # Detect if Groq manager is available
    groq = analyzer._get_groq_manager()
    source = "groq" if groq else "heuristic"

    scenes = await analyzer.analyze_script(script_text, style=style, language=language)
    return {"scenes": scenes, "scene_count": len(scenes), "source": source}