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


async def get_current_authenticated_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> str:
    """Strict authentication dependency: requires valid JWT bearer token. No guest fallback."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    token = credentials.credentials.strip()
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


ROLE_HIERARCHY = {
    "owner": 4,
    "admin": 3,
    "editor": 2,
    "viewer": 1
}


def check_role_permission(user_role: str, required_role: str) -> bool:
    """Returns True if user_role satisfies required_role in the hierarchy."""
    return ROLE_HIERARCHY.get(user_role.lower(), 0) >= ROLE_HIERARCHY.get(required_role.lower(), 0)


async def verify_workspace_access(
    workspace_id: UUID,
    user_id: UUID,
    required_role: str,
    db: AsyncSession
) -> bool:
    """Verifies if user has required_role in the organization owning workspace_id."""
    from sqlalchemy.future import select
    from app.models.models import Workspace, Organization, OrganizationMember

    # 1. Fetch workspace
    ws_query = select(Workspace).where(Workspace.id == workspace_id)
    ws_res = await db.execute(ws_query)
    workspace = ws_res.scalar_one_or_none()
    if not workspace:
        return False

    # 2. Check if user is organization owner
    org_query = select(Organization).where(Organization.id == workspace.organization_id)
    org_res = await db.execute(org_query)
    org = org_res.scalar_one_or_none()
    if org and org.owner_id == user_id:
        return True

    # 3. Check organization member role
    member_query = select(OrganizationMember).where(
        OrganizationMember.organization_id == workspace.organization_id,
        OrganizationMember.user_id == user_id
    )
    member_res = await db.execute(member_query)
    member = member_res.scalar_one_or_none()
    if not member:
        return False

    member_role_val = member.role.value if hasattr(member.role, "value") else str(member.role)
    return check_role_permission(member_role_val, required_role)


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