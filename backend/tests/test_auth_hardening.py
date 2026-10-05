import pytest
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from app.db.session import AsyncSessionLocal
from app.models.models import User, RefreshToken, AuthProvider
from app.services.auth_service import AuthService
from app.core.security import decode_token, hash_token
from app.core.config import settings
from fastapi import HTTPException

db_configured = bool(settings.DATABASE_URL and "CHANGE_ME" not in settings.DATABASE_URL)
pytestmark = pytest.mark.skipif(not db_configured, reason="Live PostgreSQL database not configured (placeholder credentials in env)")


@pytest.mark.asyncio
async def test_short_lived_access_and_refresh_tokens():
    async with AsyncSessionLocal() as db:
        user_id = uuid4()
        user = User(
            id=user_id,
            email=f"auth_{user_id}@test.com",
            full_name="Auth Hardening Tester",
            auth_provider=AuthProvider.email
        )
        db.add(user)
        await db.commit()

        service = AuthService(db)
        token_pair = await service._issue_token_pair(user)

        assert token_pair.access_token is not None
        assert token_pair.refresh_token is not None
        assert token_pair.expires_in == 15 * 60  # 15 minutes

        # Verify decoded payload has exp within 15 minutes
        payload = decode_token(token_pair.access_token)
        assert payload is not None
        assert payload["sub"] == str(user_id)


@pytest.mark.asyncio
async def test_refresh_token_rotation():
    async with AsyncSessionLocal() as db:
        user_id = uuid4()
        user = User(
            id=user_id,
            email=f"rtr_{user_id}@test.com",
            full_name="RTR Tester",
            auth_provider=AuthProvider.email
        )
        db.add(user)
        await db.commit()

        service = AuthService(db)
        initial_tokens = await service._issue_token_pair(user)
        first_refresh = initial_tokens.refresh_token

        # Rotate token
        rotated_tokens = await service.refresh_access_token(first_refresh)
        assert rotated_tokens.access_token is not None
        assert rotated_tokens.refresh_token != first_refresh

        # Check in DB that first token is marked revoked
        t1_hash = hash_token(first_refresh)
        from sqlalchemy.future import select
        t1_res = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == t1_hash))
        t1_record = t1_res.scalar_one()
        assert t1_record.is_revoked is True


@pytest.mark.asyncio
async def test_token_reuse_detection_revokes_family():
    async with AsyncSessionLocal() as db:
        user_id = uuid4()
        user = User(
            id=user_id,
            email=f"reuse_{user_id}@test.com",
            full_name="Reuse Detection Tester",
            auth_provider=AuthProvider.email
        )
        db.add(user)
        await db.commit()

        service = AuthService(db)
        initial_tokens = await service._issue_token_pair(user)
        first_refresh = initial_tokens.refresh_token

        # Legitimate rotation
        rotated_tokens = await service.refresh_access_token(first_refresh)
        second_refresh = rotated_tokens.refresh_token

        # Attacker tries to replay first_refresh!
        with pytest.raises(HTTPException) as exc:
            await service.refresh_access_token(first_refresh)
        assert exc.value.status_code == 401
        assert "reuse detected" in str(exc.value.detail).lower()

        # Both tokens in the family should now be revoked
        t2_hash = hash_token(second_refresh)
        from sqlalchemy.future import select
        t2_res = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == t2_hash))
        t2_record = t2_res.scalar_one()
        assert t2_record.is_revoked is True


@pytest.mark.asyncio
async def test_auth_logout_revokes_token():
    async with AsyncSessionLocal() as db:
        user_id = uuid4()
        user = User(
            id=user_id,
            email=f"logout_{user_id}@test.com",
            full_name="Logout Tester",
            auth_provider=AuthProvider.email
        )
        db.add(user)
        await db.commit()

        service = AuthService(db)
        tokens = await service._issue_token_pair(user)
        refresh = tokens.refresh_token

        # Logout
        await service.logout(refresh)

        # Refresh attempt should fail
        with pytest.raises(HTTPException):
            await service.refresh_access_token(refresh)
