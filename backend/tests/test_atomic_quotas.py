import asyncio
import pytest
from uuid import uuid4
from fastapi import HTTPException
from app.db.session import AsyncSessionLocal
from app.models.models import User, UserUsage, AuthProvider
from app.services.usage_service import UsageService


@pytest.mark.asyncio
async def test_atomic_quota_race_condition_single_credit():
    """
    Simulates concurrent requests when user has exactly 1 credit remaining.
    With row-locking (with_for_update), exactly 1 reservation must succeed
    and all other concurrent attempts must be rejected with HTTP 429.
    """
    user_id = uuid4()

    async with AsyncSessionLocal() as session:
        user = User(
            id=user_id,
            email=f"quota_{user_id.hex[:6]}@test.com",
            full_name="Quota Tester",
            auth_provider=AuthProvider.email,
            is_active=True
        )
        session.add(user)
        # Set user at 9 out of 10 daily generations (exactly 1 remaining)
        usage = UserUsage(
            user_id=user_id,
            ai_requests_today=0,
            video_generations_today=9,
            render_jobs_today=0
        )
        session.add(usage)
        await session.commit()

    async def try_reserve():
        async with AsyncSessionLocal() as s:
            svc = UsageService(s)
            try:
                await svc.reserve_video_generation(user_id)
                return "SUCCESS"
            except HTTPException as exc:
                if exc.status_code == 429:
                    return "RATE_LIMITED"
                raise

    # Fire 5 simultaneous reservation attempts
    results = await asyncio.gather(*[try_reserve() for _ in range(5)])

    successes = [r for r in results if r == "SUCCESS"]
    rate_limited = [r for r in results if r == "RATE_LIMITED"]

    assert len(successes) == 1, f"Expected exactly 1 success, got {len(successes)}"
    assert len(rate_limited) == 4, f"Expected 4 rate limited, got {len(rate_limited)}"

    # Confirm database state reflects exactly 10 generations (max reached)
    async with AsyncSessionLocal() as session:
        svc = UsageService(session)
        u = await svc.get_or_create_usage(user_id)
        assert u.video_generations_today == 10


@pytest.mark.asyncio
async def test_atomic_quota_release_compensation():
    """Verifies that release_video_generation decrements counter on failure."""
    user_id = uuid4()

    async with AsyncSessionLocal() as session:
        user = User(
            id=user_id,
            email=f"release_{user_id.hex[:6]}@test.com",
            full_name="Release Tester",
            auth_provider=AuthProvider.email,
            is_active=True
        )
        session.add(user)
        usage = UserUsage(
            user_id=user_id,
            video_generations_today=5
        )
        session.add(usage)
        await session.commit()

    async with AsyncSessionLocal() as session:
        svc = UsageService(session)
        await svc.reserve_video_generation(user_id)

    async with AsyncSessionLocal() as session:
        svc = UsageService(session)
        u = await svc.get_or_create_usage(user_id)
        assert u.video_generations_today == 6

        # Simulate failure compensation
        await svc.release_video_generation(user_id)

    async with AsyncSessionLocal() as session:
        svc = UsageService(session)
        u = await svc.get_or_create_usage(user_id)
        assert u.video_generations_today == 5
