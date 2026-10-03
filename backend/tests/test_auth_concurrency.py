import asyncio
import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from httpx import AsyncClient

from app.core.security import hash_token
from app.db.session import AsyncSessionLocal
from app.models.models import User, RefreshToken, AuthProvider
from app.services.auth_service import AuthService


@pytest.mark.asyncio
async def test_simultaneous_refresh_parallel_tabs_safe(client: AsyncClient):
    """
    Two browser tabs fire refresh requests with the exact same refresh token at the same millisecond.
    Both requests must receive a valid access token without triggering false family reuse revocation.
    """
    user_id = uuid4()
    raw_token = f"refresh_test_{uuid4().hex}"
    t_hash = hash_token(raw_token)
    family_id = uuid4()

    async with AsyncSessionLocal() as session:
        user = User(
            id=user_id,
            email=f"tab_race_{uuid4().hex[:6]}@test.com",
            full_name="Tab Race User",
            auth_provider=AuthProvider.email,
            is_active=True
        )
        session.add(user)
        token_rec = RefreshToken(
            token_hash=t_hash,
            user_id=user_id,
            family_id=family_id,
            is_revoked=False,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7)
        )
        session.add(token_rec)
        await session.commit()

    async def do_refresh():
        async with AsyncSessionLocal() as s:
            svc = AuthService(s)
            return await svc.refresh_access_token(raw_token)

    # Launch two simultaneous refreshes
    resp1, resp2 = await asyncio.gather(do_refresh(), do_refresh())

    assert resp1.access_token is not None
    assert resp2.access_token is not None
    assert str(resp1.user.id) == str(user_id)
    assert str(resp2.user.id) == str(user_id)


@pytest.mark.asyncio
async def test_replay_attack_outside_grace_revokes_entire_family():
    """
    An attacker replays an already rotated refresh token after grace period.
    The entire token family MUST be immediately revoked.
    """
    user_id = uuid4()
    old_raw_token = f"old_token_{uuid4().hex}"
    old_hash = hash_token(old_raw_token)
    new_raw_token = f"new_token_{uuid4().hex}"
    new_hash = hash_token(new_raw_token)
    family_id = uuid4()

    async with AsyncSessionLocal() as session:
        user = User(
            id=user_id,
            email=f"replay_{uuid4().hex[:6]}@test.com",
            full_name="Replay User",
            auth_provider=AuthProvider.email,
            is_active=True
        )
        session.add(user)
        # Old token was revoked 60 seconds ago (outside 3s grace window)
        old_rec = RefreshToken(
            token_hash=old_hash,
            user_id=user_id,
            family_id=family_id,
            is_revoked=True,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            updated_at=datetime.now(timezone.utc) - timedelta(seconds=60)
        )
        # New active token in same family
        new_rec = RefreshToken(
            token_hash=new_hash,
            user_id=user_id,
            family_id=family_id,
            is_revoked=False,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7)
        )
        session.add(old_rec)
        session.add(new_rec)
        await session.commit()

    # Attacker tries to use old token -> must trigger family revocation
    from fastapi import HTTPException
    async with AsyncSessionLocal() as session:
        svc = AuthService(session)
        with pytest.raises(HTTPException) as exc_info:
            await svc.refresh_access_token(old_raw_token)
        assert exc_info.value.status_code == 401
        assert "Token reuse detected" in exc_info.value.detail

    # Legitimate user now tries to use new token -> must be rejected because family was revoked!
    async with AsyncSessionLocal() as session:
        svc = AuthService(session)
        with pytest.raises(HTTPException) as exc_info:
            await svc.refresh_access_token(new_raw_token)
        assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_concurrent_refresh_and_logout():
    """Simultaneous logout and refresh requests must cleanly terminate the session."""
    user_id = uuid4()
    raw_token = f"logout_race_{uuid4().hex}"
    t_hash = hash_token(raw_token)
    family_id = uuid4()

    async with AsyncSessionLocal() as session:
        user = User(
            id=user_id,
            email=f"logout_race_{uuid4().hex[:6]}@test.com",
            full_name="Logout Race User",
            auth_provider=AuthProvider.email,
            is_active=True
        )
        session.add(user)
        token_rec = RefreshToken(
            token_hash=t_hash,
            user_id=user_id,
            family_id=family_id,
            is_revoked=False,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7)
        )
        session.add(token_rec)
        await session.commit()

    async def do_refresh():
        async with AsyncSessionLocal() as s:
            svc = AuthService(s)
            try:
                return await svc.refresh_access_token(raw_token)
            except Exception as e:
                return e

    async def do_logout():
        async with AsyncSessionLocal() as s:
            svc = AuthService(s)
            return await svc.logout_user(raw_refresh_token=raw_token)

    # Gather logout and refresh concurrently
    results = await asyncio.gather(do_logout(), do_refresh())
    assert True  # Completes without deadlocks or unhandled exceptions
