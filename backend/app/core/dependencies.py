from typing import AsyncGenerator, Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.core.security import decode_token

security_scheme = HTTPBearer(auto_error=False)

DEFAULT_GUEST_USER_ID = "595744ab-c375-4bec-a3c0-429113163fe1"


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_current_user_id(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)) -> str:
    if not credentials or not credentials.credentials:
        return DEFAULT_GUEST_USER_ID

    token = credentials.credentials
    if token in ["guest_studio_session_token", "guest_studio_token", "null", "undefined"]:
        return DEFAULT_GUEST_USER_ID

    payload = decode_token(token)
    if not payload or "sub" not in payload:
        return DEFAULT_GUEST_USER_ID

    try:
        UUID(str(payload["sub"]))
        return str(payload["sub"])
    except Exception:
        return DEFAULT_GUEST_USER_ID