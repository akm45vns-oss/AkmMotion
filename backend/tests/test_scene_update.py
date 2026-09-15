import pytest
import uuid
from httpx import AsyncClient
from app.db.session import AsyncSessionLocal
from app.models.models import User, Project, Script, Scene, AnimationStyle
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_update_scene_succeeds_for_owner(client: AsyncClient):
    user_id = uuid.uuid4()
    project_id = uuid.uuid4()
    script_id = uuid.uuid4()
    scene_id = uuid.uuid4()

    async with AsyncSessionLocal() as session:
        user = User(id=user_id, email=f"owner_{uuid.uuid4().hex[:6]}@test.com", full_name="Scene Owner")
        session.add(user)
        project = Project(id=project_id, user_id=user_id, title="Owner Project")
        session.add(project)
        script = Script(id=script_id, project_id=project_id, content="Authoritative script content.")
        session.add(script)
        scene = Scene(
            id=scene_id,
            project_id=project_id,
            script_id=script_id,
            scene_number=1,
            narration="Authoritative script content.",
            subtitle="Authoritative script content.",
            image_prompt="A wide shot of mountains at dawn.",
            animation_style=AnimationStyle.ken_burns,
            duration=3.2
        )
        session.add(scene)
        await session.commit()

    token = create_access_token(subject=str(user_id))

    # Perform update: animation=zoom, duration=5.0, image_prompt, subtitle
    payload = {
        "narration": "Authoritative script content.",
        "subtitle": "Authoritative script content.",
        "image_prompt": "A cinematic shot of mountains with golden hour sunlight.",
        "animation_style": "zoom",
        "duration": 5.0
    }

    res = await client.put(
        f"/api/v1/scenes/{scene_id}",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert res.status_code == 200
    data = res.json()
    assert data["id"] == str(scene_id)
    assert data["duration"] == 5.0
    assert data["animation_style"] == "zoom"
    assert data["image_prompt"] == "A cinematic shot of mountains with golden hour sunlight."
    assert data["subtitle"] == "Authoritative script content."


@pytest.mark.asyncio
async def test_update_scene_rejects_unauthorized_user(client: AsyncClient):
    owner_id = uuid.uuid4()
    attacker_id = uuid.uuid4()
    project_id = uuid.uuid4()
    script_id = uuid.uuid4()
    scene_id = uuid.uuid4()

    async with AsyncSessionLocal() as session:
        owner = User(id=owner_id, email=f"owner_{uuid.uuid4().hex[:6]}@test.com", full_name="Owner")
        attacker = User(id=attacker_id, email=f"attacker_{uuid.uuid4().hex[:6]}@test.com", full_name="Attacker")
        session.add_all([owner, attacker])
        project = Project(id=project_id, user_id=owner_id, title="Protected Project")
        session.add(project)
        script = Script(id=script_id, project_id=project_id, content="Protected Script")
        session.add(script)
        scene = Scene(
            id=scene_id,
            project_id=project_id,
            script_id=script_id,
            scene_number=1,
            narration="Protected Script",
            subtitle="Protected Script",
            image_prompt="Protected prompt",
            animation_style=AnimationStyle.ken_burns,
            duration=3.2
        )
        session.add(scene)
        await session.commit()

    attacker_token = create_access_token(subject=str(attacker_id))

    # Attacker tries to modify owner's scene
    payload = {
        "duration": 10.0,
        "animation_style": "pan"
    }

    res = await client.put(
        f"/api/v1/scenes/{scene_id}",
        json=payload,
        headers={"Authorization": f"Bearer {attacker_token}"}
    )

    # Must be 404 (IDOR isolation)
    assert res.status_code == 404
    assert res.json()["detail"] == "Scene not found"


@pytest.mark.asyncio
async def test_scene_update_persists_across_reload(client: AsyncClient):
    user_id = uuid.uuid4()
    project_id = uuid.uuid4()
    script_id = uuid.uuid4()
    scene_id = uuid.uuid4()

    async with AsyncSessionLocal() as session:
        user = User(id=user_id, email=f"user_{uuid.uuid4().hex[:6]}@test.com", full_name="Persistence User")
        session.add(user)
        project = Project(id=project_id, user_id=user_id, title="Persistence Project")
        session.add(project)
        script = Script(id=script_id, project_id=project_id, content="Persistence Script")
        session.add(script)
        scene = Scene(
            id=scene_id,
            project_id=project_id,
            script_id=script_id,
            scene_number=1,
            narration="Persistence Script",
            subtitle="Persistence Script",
            image_prompt="Initial prompt",
            animation_style=AnimationStyle.ken_burns,
            duration=3.2
        )
        session.add(scene)
        await session.commit()

    token = create_access_token(subject=str(user_id))

    # Update 3.2s -> 5.0s, ken_burns -> zoom
    update_res = await client.put(
        f"/api/v1/scenes/{scene_id}",
        json={
            "duration": 5.0,
            "animation_style": "zoom",
            "image_prompt": "Persisted prompt",
            "subtitle": "Persisted subtitle"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert update_res.status_code == 200

    # Simulate page refresh by querying GET /api/v1/scenes/project/{project_id}
    fetch_res = await client.get(
        f"/api/v1/scenes/project/{project_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert fetch_res.status_code == 200
    scenes = fetch_res.json()
    assert len(scenes) == 1
    reloaded_scene = scenes[0]

    assert reloaded_scene["duration"] == 5.0
    assert reloaded_scene["animation_style"] == "zoom"
    assert reloaded_scene["image_prompt"] == "Persisted prompt"
    assert reloaded_scene["subtitle"] == "Persisted subtitle"


@pytest.mark.asyncio
async def test_update_scene_rejects_invalid_extra_fields(client: AsyncClient):
    user_id = uuid.uuid4()
    project_id = uuid.uuid4()
    script_id = uuid.uuid4()
    scene_id = uuid.uuid4()

    async with AsyncSessionLocal() as session:
        user = User(id=user_id, email=f"strict_{uuid.uuid4().hex[:6]}@test.com", full_name="Strict")
        session.add(user)
        project = Project(id=project_id, user_id=user_id, title="Strict Project")
        session.add(project)
        script = Script(id=script_id, project_id=project_id, content="Strict Script")
        session.add(script)
        scene = Scene(
            id=scene_id,
            project_id=project_id,
            script_id=script_id,
            scene_number=1,
            narration="Strict Script",
            subtitle="Strict Script",
            image_prompt="Strict prompt",
            animation_style=AnimationStyle.ken_burns,
            duration=3.2
        )
        session.add(scene)
        await session.commit()

    token = create_access_token(subject=str(user_id))

    # Sending invalid/extra field not in schema
    res = await client.put(
        f"/api/v1/scenes/{scene_id}",
        json={"invalid_invented_field": "hacking", "duration": 5.0},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 422
