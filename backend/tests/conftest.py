import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.session import engine
from app.core.rate_limit import _rate_limiter


@pytest.fixture(autouse=True)
async def cleanup_after_test():
    """Clean up DB connections and rate limiter after each test."""
    _rate_limiter.reset()
    yield
    await engine.dispose()
    _rate_limiter.reset()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

