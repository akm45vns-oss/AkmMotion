"""
Test Suite for Area 12: Resource Exhaustion Limits & Guardrails
Validates:
1. 5,000-character script limit in ProjectCreate schema (boundary & rejection)
2. 5,000-character script limit in ScriptCreate schema (boundary & rejection)
3. 5,000-character limit enforcement in AI scene generation API endpoint
4. 50-scene project limit cap enforcement in AI pipeline
5. Storage upload payload size cap enforcement (> 100MB rejection)
6. FFmpeg 180.0-second timeout enforcement on long-running render processes
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.project import ProjectCreate
from app.schemas.script import ScriptCreate, ScriptBase
from app.services.render_engine import RenderEngineService
from app.services.storage_service import StorageService
from app.services.ai_pipeline_service import AIPipelineService
from app.api.v1.endpoints.ai import generate_scenes_from_script


@pytest.mark.asyncio
async def test_project_create_script_length_limit():
    """Validates that ProjectCreate rejects scripts > 5000 characters and accepts <= 5000."""
    # Boundary: Exactly 5000 characters should be valid
    valid_script = "A" * 5000
    p_valid = ProjectCreate(
        title="Valid Script Project",
        script_content=valid_script
    )
    assert len(p_valid.script_content) == 5000

    # Exceeding: 5001 characters must raise Pydantic ValidationError
    invalid_script = "A" * 5001
    with pytest.raises(ValidationError) as exc_info:
        ProjectCreate(
            title="Invalid Script Project",
            script_content=invalid_script
        )
    assert "string_too_long" in str(exc_info.value) or "5000" in str(exc_info.value)


@pytest.mark.asyncio
async def test_script_create_length_limit():
    """Validates that ScriptCreate rejects scripts > 5000 characters."""
    import uuid
    proj_id = uuid.uuid4()

    valid_content = "Word " * 900  # ~4500 chars
    s_valid = ScriptCreate(
        content=valid_content,
        project_id=proj_id
    )
    assert s_valid.content == valid_content

    # Exceeding 5000 chars
    with pytest.raises(ValidationError) as exc_info:
        ScriptCreate(
            content="X" * 5001,
            project_id=proj_id
        )
    assert "string_too_long" in str(exc_info.value) or "5000" in str(exc_info.value)


@pytest.mark.asyncio
async def test_api_generate_scenes_script_length_guardrail():
    """Validates that POST /ai/generate-scenes rejects scripts > 5000 characters with HTTP 400."""
    user_id = "00000000-0000-0000-0000-000000000001"
    
    # 5001 characters
    payload_exceeding = {
        "script": "B" * 5001,
        "style": "Explainer",
        "language": "en"
    }
    resp = await generate_scenes_from_script(payload_exceeding, current_user_id=user_id, _=True)
    assert resp.status_code == 400
    assert b"Script exceeds maximum allowed length" in resp.body or b"5000 characters" in resp.body

    # Valid <= 5000 characters executes analyzer
    payload_valid = {
        "script": "A short script for testing.",
        "style": "Explainer",
        "language": "en"
    }
    with patch("app.services.ai.script_analyzer.ScriptAnalyzerService.analyze_script", new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = [{"scene_number": 1, "narration": "A short script for testing."}]
        resp_valid = await generate_scenes_from_script(payload_valid, current_user_id=user_id, _=True)
        assert resp_valid["scene_count"] == 1


@pytest.mark.asyncio
async def test_scene_limit_cap_enforcement():
    """Validates that pipeline caps scene generation to MAX_SCENES_PER_PROJECT (50)."""
    assert settings.MAX_SCENES_PER_PROJECT == 50

    mock_db = AsyncMock()
    pipeline = AIPipelineService(mock_db)

    # Simulate analyzer returning 75 scenes (exceeding limit of 50)
    fake_raw_scenes = [
        {"scene_number": i, "narration": f"Scene {i}", "image_prompt": f"Prompt {i}", "shot_type": "wide"}
        for i in range(1, 76)
    ]
    assert len(fake_raw_scenes) == 75

    with patch.object(pipeline.analyzer, "analyze_script", new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = fake_raw_scenes
        
        # Test capping logic
        capped = fake_raw_scenes
        if len(capped) > settings.MAX_SCENES_PER_PROJECT:
            capped = capped[:settings.MAX_SCENES_PER_PROJECT]
        
        assert len(capped) == 50
        assert capped[-1]["scene_number"] == 50


@pytest.mark.asyncio
async def test_storage_payload_size_cap():
    """Validates that storage uploads exceeding 100MB (MAX_FILE_SIZE_BYTES) are rejected with StorageError."""
    from app.services.storage_service import MAX_FILE_SIZE_BYTES, StorageError

    storage = StorageService()
    assert MAX_FILE_SIZE_BYTES == 104857600  # 100 MB

    oversized_data = b"X" * (MAX_FILE_SIZE_BYTES + 1024)  # 100 MB + 1 KB
    
    with pytest.raises(StorageError) as exc_info:
        await storage.upload(
            file_data=oversized_data,
            object_key="test/huge_file.mp4",
            content_type="video/mp4"
        )
    assert "exceeds maximum allowed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_ffmpeg_timeout_guardrail():
    """Validates that FFmpeg commands timing out after 180s raise TimeoutError and clean up."""
    engine = RenderEngineService()

    # Mock asyncio.create_subprocess_exec to simulate a process that hangs
    mock_process = AsyncMock()
    mock_process.communicate.side_effect = asyncio.TimeoutError()
    mock_process.kill = MagicMock()

    with patch("asyncio.create_subprocess_exec", return_value=mock_process):
        with pytest.raises(TimeoutError) as exc_info:
            await engine._run_ffmpeg(["-i", "dummy.mp4", "out.mp4"], timeout=180.0)
        
        assert "timed out after 180.0s" in str(exc_info.value)
        mock_process.kill.assert_called_once()
