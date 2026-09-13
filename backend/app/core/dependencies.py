from typing import AsyncGenerator, Optional
from uuid import UUID, uuid4
from fastapi import Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.core.security import decode_token
from app.core.config import settings

security_scheme = HTTPBearer(auto_error=False)

GUEST_SESSION_COOKIE = "guest_session_id"
GUEST_SESSION_HEADER = "X-Guest-Session-ID"


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


async def get_current_user_id(
    request: Request,
    response: Response,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> str:
    # 1. Check for JWT token in Authorization header
    if credentials and credentials.credentials:
        token = credentials.credentials.strip()
        # If not an explicit guest placeholder token, enforce strict JWT validation
        if token not in ["guest_studio_session_token", "guest_studio_token", "null", "undefined", ""]:
            payload = decode_token(token)
            if not payload or "sub" not in payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired authentication token",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            try:
                sub_uuid = UUID(str(payload["sub"]))
                return str(sub_uuid)
            except (ValueError, TypeError):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid user identifier in token",
                    headers={"WWW-Authenticate": "Bearer"}
                )

    # 2. Guest user: use cookie or header-based isolated session ID
    raw_guest_id = (
        request.cookies.get(GUEST_SESSION_COOKIE)
        or request.headers.get(GUEST_SESSION_HEADER)
        or request.headers.get("x-guest-session-id")
    )

    valid_guest = False
    guest_session_id = None
    if raw_guest_id:
        try:
            parsed_uuid = UUID(str(raw_guest_id).strip())
            guest_session_id = str(parsed_uuid)
            valid_guest = True
        except (ValueError, TypeError):
            valid_guest = False

    if not valid_guest:
        guest_session_id = str(uuid4())
        is_secure = (
            request.url.scheme == "https"
            or request.headers.get("x-forwarded-proto", "").lower() == "https"
            or settings.ENVIRONMENT.lower() in ["production", "prod"]
        )
        response.set_cookie(
            key=GUEST_SESSION_COOKIE,
            value=guest_session_id,
            httponly=True,
            secure=is_secure,
            samesite="lax",
            path="/",
            max_age=86400 * 30  # 30 days
        )

    return guest_session_id


async def ensure_user_in_db(db: AsyncSession, user_id: UUID, is_guest: bool = True) -> None:
    """
    Ensures that a user record exists in the users table so that foreign key
    constraints in projects, characters, user_settings, and render_jobs succeed.
    For guest users, creates an isolated guest profile if not already present.
    """
    from app.models.models import User, AuthProvider
    from sqlalchemy.future import select

    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if not user:
        try:
            guest_user = User(
                id=user_id,
                email=f"guest_{user_id}@guest.akmmotion.internal",
                full_name="Guest User" if is_guest else "User",
                auth_provider=AuthProvider.email,
                is_active=True,
                is_verified=False
            )
            db.add(guest_user)
            await db.commit()
        except Exception:
            await db.rollback()