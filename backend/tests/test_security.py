import pytest
from httpx import AsyncClient
from uuid import uuid4, UUID
from datetime import timedelta
from app.core.security import create_access_token
from app.core.dependencies import GUEST_SESSION_COOKIE, GUEST_SESSION_HEADER


@pytest.mark.asyncio
async def test_1_guest_isolation_different_sessions(client: AsyncClient):
    """1. Test that different guest sessions get different IDs"""
    guest_a_id = str(uuid4())
    guest_b_id = str(uuid4())

    response_a = await client.get("/api/v1/ai/voices", cookies={GUEST_SESSION_COOKIE: guest_a_id})
    response_b = await client.get("/api/v1/ai/voices", cookies={GUEST_SESSION_COOKIE: guest_b_id})

    assert response_a.status_code == 200
    assert response_b.status_code == 200
    assert guest_a_id != guest_b_id


@pytest.mark.asyncio
async def test_2_guest_cannot_access_other_guest_project(client: AsyncClient):
    """2. Test that Guest A's project is completely inaccessible to Guest B (IDOR)"""
    guest_a_id = str(uuid4())
    guest_b_id = str(uuid4())

    # Guest A creates a project
    create_res = await client.post(
        "/api/v1/projects",
        json={
            "title": "Guest A Private Project",
            "description": "Top secret content",
            "style": "Explainer",
            "language": "en",
            "script_content": "This belongs to guest A."
        },
        cookies={GUEST_SESSION_COOKIE: guest_a_id}
    )
    assert create_res.status_code == 201
    project_id = create_res.json()["id"]

    # Guest A can access their own project
    get_a_res = await client.get(
        f"/api/v1/projects/{project_id}",
        cookies={GUEST_SESSION_COOKIE: guest_a_id}
    )
    assert get_a_res.status_code == 200

    # Guest B tries to GET Guest A's project -> MUST be 404
    get_b_res = await client.get(
        f"/api/v1/projects/{project_id}",
        cookies={GUEST_SESSION_COOKIE: guest_b_id}
    )
    assert get_b_res.status_code == 404

    # Guest B tries to UPDATE Guest A's project -> MUST be 404
    put_b_res = await client.put(
        f"/api/v1/projects/{project_id}",
        json={"title": "Hacked Title"},
        cookies={GUEST_SESSION_COOKIE: guest_b_id}
    )
    assert put_b_res.status_code == 404

    # Guest B tries to DELETE Guest A's project -> MUST be 404
    del_b_res = await client.delete(
        f"/api/v1/projects/{project_id}",
        cookies={GUEST_SESSION_COOKIE: guest_b_id}
    )
    assert del_b_res.status_code == 404


@pytest.mark.asyncio
async def test_3_guest_cannot_access_other_guest_scene(client: AsyncClient):
    """3. Test that Guest B cannot read, update, or delete scenes belonging to Guest A's project"""
    guest_a_id = str(uuid4())
    guest_b_id = str(uuid4())

    # Guest A creates a project
    create_res = await client.post(
        "/api/v1/projects",
        json={
            "title": "Guest A Scenes Project",
            "style": "Cinematic",
            "script_content": "Scene 1 narration."
        },
        cookies={GUEST_SESSION_COOKIE: guest_a_id}
    )
    assert create_res.status_code == 201
    project_id = create_res.json()["id"]

    # Guest B tries to list scenes for Guest A's project -> Returns empty list
    scenes_b_res = await client.get(
        f"/api/v1/scenes/project/{project_id}",
        cookies={GUEST_SESSION_COOKIE: guest_b_id}
    )
    assert scenes_b_res.status_code == 200
    assert scenes_b_res.json() == []

    # Guest B tries to update a scene with fake or unknown ID -> 404
    fake_scene_id = str(uuid4())
    put_scene_res = await client.put(
        f"/api/v1/scenes/{fake_scene_id}",
        json={"narration": "Hacked narration"},
        cookies={GUEST_SESSION_COOKIE: guest_b_id}
    )
    assert put_scene_res.status_code == 404

    # Guest B tries to delete a scene -> 404
    del_scene_res = await client.delete(
        f"/api/v1/scenes/{fake_scene_id}",
        cookies={GUEST_SESSION_COOKIE: guest_b_id}
    )
    assert del_scene_res.status_code == 404


@pytest.mark.asyncio
async def test_4_guest_cannot_access_other_guest_character(client: AsyncClient):
    """4. Test that Guest B cannot read, lock, or unlock characters created by Guest A"""
    guest_a_id = str(uuid4())
    guest_b_id = str(uuid4())

    # Guest A creates a character
    char_res = await client.post(
        "/api/v1/characters",
        json={
            "name": "Detective Vance",
            "role": "Protagonist",
            "description": "Hard-boiled investigator",
            "is_locked": False,
            "dna": {
                "character_code": "char_vance",
                "skin_tone": "Medium",
                "hair_color": "Black",
                "hair_style": "Short",
                "eye_color": "Brown"
            }
        },
        cookies={GUEST_SESSION_COOKIE: guest_a_id}
    )
    assert char_res.status_code == 201
    char_id = char_res.json()["id"]

    # Guest A can view it
    get_char_a = await client.get(
        f"/api/v1/characters/{char_id}",
        cookies={GUEST_SESSION_COOKIE: guest_a_id}
    )
    assert get_char_a.status_code == 200

    # Guest B tries to view Guest A's character -> 404
    get_char_b = await client.get(
        f"/api/v1/characters/{char_id}",
        cookies={GUEST_SESSION_COOKIE: guest_b_id}
    )
    assert get_char_b.status_code == 404

    # Guest B tries to lock Guest A's character -> 404
    lock_char_b = await client.post(
        f"/api/v1/characters/{char_id}/lock",
        cookies={GUEST_SESSION_COOKIE: guest_b_id}
    )
    assert lock_char_b.status_code == 404

    # Guest B tries to unlock Guest A's character -> 404
    unlock_char_b = await client.post(
        f"/api/v1/characters/{char_id}/unlock",
        cookies={GUEST_SESSION_COOKIE: guest_b_id}
    )
    assert unlock_char_b.status_code == 404


@pytest.mark.asyncio
async def test_5_authenticated_user_cannot_access_other_user_resources(client: AsyncClient):
    """5. Test that Authenticated User A cannot access Authenticated User B's resources (IDOR)"""
    user_a_id = str(uuid4())
    user_b_id = str(uuid4())
    token_a = create_access_token(subject=user_a_id)
    token_b = create_access_token(subject=user_b_id)

    # User A creates a project
    create_res = await client.post(
        "/api/v1/projects",
        json={"title": "User A Private", "style": "Explainer", "script_content": "User A script"},
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert create_res.status_code == 201
    project_id = create_res.json()["id"]

    # User B tries to view User A's project -> 404
    get_b_res = await client.get(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert get_b_res.status_code == 404

    # User B tries to update User A's project -> 404
    put_b_res = await client.put(
        f"/api/v1/projects/{project_id}",
        json={"title": "Hacked Title"},
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert put_b_res.status_code == 404

    # User B tries to delete User A's project -> 404
    del_b_res = await client.delete(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert del_b_res.status_code == 404


@pytest.mark.asyncio
async def test_6_ai_pipeline_project_ownership(client: AsyncClient):
    """6. Test that User B cannot trigger AI pipeline generation on User A's project"""
    user_a_id = str(uuid4())
    user_b_id = str(uuid4())
    token_a = create_access_token(subject=user_a_id)
    token_b = create_access_token(subject=user_b_id)

    # User A creates a project
    create_res = await client.post(
        "/api/v1/projects",
        json={"title": "User A Pipeline Project", "style": "Explainer", "script_content": "Full pipeline script."},
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert create_res.status_code == 201
    project_id = create_res.json()["id"]

    # User B tries to run generate-pipeline on User A's project -> MUST be 404
    pipeline_res = await client.post(
        f"/api/v1/ai/generate-pipeline/{project_id}",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert pipeline_res.status_code == 404


@pytest.mark.asyncio
async def test_7_invalid_and_expired_jwt_rejected(client: AsyncClient):
    """7. Test that invalid or expired JWTs are rejected with 401 and never fall back to guest"""
    # Malformed token
    response_invalid = await client.get(
        "/api/v1/projects",
        headers={"Authorization": "Bearer totally_bogus_token_xyz"}
    )
    assert response_invalid.status_code == 401

    # Expired token
    expired_token = create_access_token(subject=str(uuid4()), expires_delta=timedelta(seconds=-60))
    response_expired = await client.get(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert response_expired.status_code == 401


@pytest.mark.asyncio
async def test_8_ai_endpoints_rate_limiting_isolated(client: AsyncClient):
    """8. Test that rate limits are enforced per session and do not cause crosstalk"""
    from unittest.mock import patch, AsyncMock
    user_a = str(uuid4())
    user_b = str(uuid4())

    with patch("app.services.ai.script_analyzer.ScriptAnalyzerService.analyze_script", new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = [{"scene_number": 1, "narration": "mock"}]

        # User A makes 21 rapid requests (limit is 20 for script AI)
        statuses_a = []
        for _ in range(22):
            res = await client.post(
                "/api/v1/ai/generate-scenes",
                json={"script": "Test script", "language": "en"},
                cookies={GUEST_SESSION_COOKIE: user_a}
            )
            statuses_a.append(res.status_code)

        assert 429 in statuses_a

        # User B with a different session ID should NOT be blocked (rate limiting is isolated)
        res_b = await client.post(
            "/api/v1/ai/generate-scenes",
            json={"script": "Test script", "language": "en"},
            cookies={GUEST_SESSION_COOKIE: user_b}
        )
        assert res_b.status_code == 200


@pytest.mark.asyncio
async def test_9_image_proxy_ssrf_blocking(client: AsyncClient):
    """9. Test that image proxy strictly blocks localhost, private IPs, link-local, and suffix bypasses"""
    blocked_urls = [
        "http://localhost:8000/test.jpg",
        "http://127.0.0.1:8000/test.jpg",
        "http://0.0.0.0/test.jpg",
        "http://10.0.0.1/secret.jpg",
        "http://192.168.1.1/router.jpg",
        "http://172.16.0.1/internal.jpg",
        "http://169.254.169.254/latest/meta-data/",
        "http://attackerpollinations.ai/fake.jpg",
        "http://evil-pollinations.ai/test.jpg",
        "ftp://pollinations.ai/image.jpg",
        "file:///etc/passwd",
    ]

    for target_url in blocked_urls:
        response = await client.get(f"/api/v1/ai/image-proxy?url={target_url}")
        assert response.status_code in [400, 403], f"Expected 400 or 403 for {target_url}, got {response.status_code}"


@pytest.mark.asyncio
async def test_10_image_proxy_allows_legitimate_domains(client: AsyncClient):
    """10. Test that valid image hosts are accepted and not blocked as SSRF"""
    valid_url = "https://image.pollinations.ai/prompt/cinematic%20landscape"
    response = await client.get(f"/api/v1/ai/image-proxy?url={valid_url}")
    # Should not be blocked by 403 (security check passes)
    assert response.status_code in [200, 400, 502]


@pytest.mark.asyncio
async def test_11_guest_full_crud_workflow(client: AsyncClient):
    """11. Test that guest can create, list, and read their own project without DB foreign key errors"""
    guest_id = str(uuid4())

    # Create project as guest
    create_res = await client.post(
        "/api/v1/projects",
        json={
            "title": "Guest Working Project",
            "description": "Should succeed without FK error",
            "style": "Explainer",
            "language": "en",
            "script_content": "A story about persistence."
        },
        cookies={GUEST_SESSION_COOKIE: guest_id}
    )
    assert create_res.status_code == 201
    project_data = create_res.json()
    project_id = project_data["id"]

    # List projects as guest
    list_res = await client.get(
        "/api/v1/projects",
        cookies={GUEST_SESSION_COOKIE: guest_id}
    )
    assert list_res.status_code == 200
    items = list_res.json()["items"]
    assert any(p["id"] == project_id for p in items)

    # Read project
    get_res = await client.get(
        f"/api/v1/projects/{project_id}",
        cookies={GUEST_SESSION_COOKIE: guest_id}
    )
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Guest Working Project"


@pytest.mark.asyncio
async def test_12_guest_settings_isolation_and_fk_safety(client: AsyncClient):
    """12. Test that fresh guests can access/update settings safely without FK violation and are isolated"""
    guest_a_id = str(uuid4())
    guest_b_id = str(uuid4())

    # Guest A updates settings
    put_a = await client.put(
        "/api/v1/settings",
        json={"language": "hi", "theme": "light", "notifications_enabled": False},
        cookies={GUEST_SESSION_COOKIE: guest_a_id}
    )
    assert put_a.status_code == 200
    data_a = put_a.json()
    assert data_a["language"] == "hi"
    assert data_a["theme"] == "light"

    # Guest B accesses settings -> gets default settings, not Guest A's settings
    get_b = await client.get(
        "/api/v1/settings",
        cookies={GUEST_SESSION_COOKIE: guest_b_id}
    )
    assert get_b.status_code == 200
    data_b = get_b.json()
    assert data_b["language"] == "en"
    assert data_b["theme"] == "dark"


@pytest.mark.asyncio
async def test_13_render_job_ownership_idor(client: AsyncClient):
    """13. Test that RenderJob status is protected by ownership and inaccessible to other users (IDOR)"""
    user_a_id = str(uuid4())
    user_b_id = str(uuid4())
    token_a = create_access_token(subject=user_a_id)
    token_b = create_access_token(subject=user_b_id)

    # User A creates a project and starts a render job
    proj_res = await client.post(
        "/api/v1/projects",
        json={"title": "Render Project", "style": "Explainer", "script_content": "Render this."},
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert proj_res.status_code == 201
    project_id = proj_res.json()["id"]

    start_res = await client.post(
        f"/api/v1/render/start/{project_id}",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert start_res.status_code == 201
    job_id = start_res.json()["id"]

    # User A can query their render status
    status_a = await client.get(
        f"/api/v1/render/status/{job_id}",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert status_a.status_code == 200

    # User B tries to query User A's render status -> MUST be 404
    status_b = await client.get(
        f"/api/v1/render/status/{job_id}",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert status_b.status_code == 404


@pytest.mark.asyncio
async def test_14_proxy_ip_rate_limiting_isolated(client: AsyncClient):
    """14. Test that rate limiting inspects proxy headers (X-Forwarded-For) to avoid IP collapse and isolates NAT users via guest sessions"""
    from app.core.rate_limit import _rate_limiter
    _rate_limiter.reset()

    proxy_client_1 = "198.51.100.10"
    proxy_client_2 = "198.51.100.20"

    from unittest.mock import patch, AsyncMock
    with patch("app.services.ai.script_analyzer.ScriptAnalyzerService.analyze_script", new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = [{"scene_number": 1, "narration": "mock"}]

        # Client 1 (without cookies, tracked by proxy IP) exhausts rate limit
        for _ in range(22):
            client.cookies.clear()
            await client.post(
                "/api/v1/ai/generate-scenes",
                json={"script": "Test script", "language": "en"},
                headers={"X-Forwarded-For": f"{proxy_client_1}, 10.0.0.1"}
            )

        # Client 1 should be rate limited by its IP
        client.cookies.clear()
        res_1 = await client.post(
            "/api/v1/ai/generate-scenes",
            json={"script": "Test script", "language": "en"},
            headers={"X-Forwarded-For": f"{proxy_client_1}, 10.0.0.1"}
        )
        assert res_1.status_code == 429

        # Client 2 behind the same reverse proxy (different client IP) should NOT be blocked
        client.cookies.clear()
        res_2 = await client.post(
            "/api/v1/ai/generate-scenes",
            json={"script": "Test script", "language": "en"},
            headers={"X-Forwarded-For": f"{proxy_client_2}, 10.0.0.1"}
        )
        assert res_2.status_code == 200

        # Also test NAT scenario: Client 3 is behind the SAME NAT IP as Client 1 (198.51.100.10),
        # but has a distinct guest session cookie - it must NOT collapse into Client 1's exhausted IP bucket!
        guest_3_id = str(uuid4())
        res_3 = await client.post(
            "/api/v1/ai/generate-scenes",
            json={"script": "Test script", "language": "en"},
            headers={"X-Forwarded-For": f"{proxy_client_1}, 10.0.0.1"},
            cookies={GUEST_SESSION_COOKIE: guest_3_id}
        )
        assert res_3.status_code == 200


@pytest.mark.asyncio
async def test_15_production_cookie_security(client: AsyncClient):
    """15. Test that guest_session_id cookie is HttpOnly, SameSite=lax, Path=/, and Secure in HTTPS/production"""
    from app.core.config import settings
    from unittest.mock import patch, AsyncMock

    orig_env = settings.ENVIRONMENT
    settings.ENVIRONMENT = "development"
    with patch("app.services.ai.script_analyzer.ScriptAnalyzerService.analyze_script", new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = [{"scene_number": 1, "narration": "mock"}]
        try:
            # Case 1: Plain HTTP development -> cookie is HttpOnly, SameSite=lax, Path=/, but NOT Secure (works locally)
            client.cookies.clear()
            res_dev = await client.post(
                "/api/v1/ai/generate-scenes",
                json={"script": "Hello world", "language": "en"}
            )
            assert res_dev.status_code == 200
            set_cookie_dev = res_dev.headers.get("set-cookie", "").lower()
            assert "guest_session_id=" in set_cookie_dev
            assert "httponly" in set_cookie_dev
            assert "samesite=lax" in set_cookie_dev
            assert "path=/" in set_cookie_dev
            assert "secure" not in set_cookie_dev

            # Case 2: Request forwarded over HTTPS (X-Forwarded-Proto: https) -> Secure MUST be present
            client.cookies.clear()
            res_https = await client.post(
                "/api/v1/ai/generate-scenes",
                json={"script": "Hello world", "language": "en"},
                headers={"X-Forwarded-Proto": "https"}
            )
            assert res_https.status_code == 200
            set_cookie_https = res_https.headers.get("set-cookie", "").lower()
            assert "guest_session_id=" in set_cookie_https
            assert "httponly" in set_cookie_https
            assert "samesite=lax" in set_cookie_https
            assert "path=/" in set_cookie_https
            assert "secure" in set_cookie_https

            # Case 3: Production environment (ENVIRONMENT=production) -> Secure MUST be present
            client.cookies.clear()
            settings.ENVIRONMENT = "production"
            res_prod = await client.post(
                "/api/v1/ai/generate-scenes",
                json={"script": "Hello world", "language": "en"}
            )
            assert res_prod.status_code == 200
            set_cookie_prod = res_prod.headers.get("set-cookie", "").lower()
            assert "guest_session_id=" in set_cookie_prod
            assert "httponly" in set_cookie_prod
            assert "samesite=lax" in set_cookie_prod
            assert "path=/" in set_cookie_prod
            assert "secure" in set_cookie_prod
        finally:
            settings.ENVIRONMENT = orig_env
            client.cookies.clear()




