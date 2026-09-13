import pytest
from httpx import AsyncClient
from app.core.security import create_access_token, decode_token
from app.services.ai.script_analyzer import ScriptAnalyzerService
from app.services.render_engine import RenderEngineService


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "AkmMotion API"


@pytest.mark.asyncio
async def test_ai_voices_endpoint(client: AsyncClient):
    response = await client.get("/api/v1/ai/voices")
    assert response.status_code == 200
    voices = response.json()
    assert len(voices) >= 6
    assert any(v["id"] == "voice_alloy" for v in voices)


@pytest.mark.asyncio
async def test_ai_styles_endpoint(client: AsyncClient):
    response = await client.get("/api/v1/ai/styles")
    assert response.status_code == 200
    styles = response.json()
    assert len(styles) >= 6
    assert any(s["id"] == "Explainer" for s in styles)


def test_jwt_token_generation_and_decoding():
    user_id = "11111111-2222-3333-4444-555555555555"
    token = create_access_token(subject=user_id)
    assert token is not None

    decoded = decode_token(token)
    assert decoded is not None
    assert decoded["sub"] == user_id


@pytest.mark.asyncio
async def test_script_analyzer_heuristic_split():
    analyzer = ScriptAnalyzerService()
    script = "AI is changing the world. It automates video creation. Creators can produce content 10x faster."
    scenes = await analyzer.analyze_script(script, style="Explainer", language="en")
    
    assert len(scenes) >= 2
    assert "scene_number" in scenes[0]
    assert "narration" in scenes[0]
    assert "image_prompt" in scenes[0]


@pytest.mark.asyncio
async def test_render_engine_compilation():
    engine = RenderEngineService()
    
    progress_records = []
    async def mock_progress(pct: int, msg: str):
        progress_records.append(pct)

    video_url = await engine.compile_video(
        scenes_data=[],
        output_path="",
        progress_callback=mock_progress
    )

    assert video_url.startswith("http")
    assert 100 in progress_records
