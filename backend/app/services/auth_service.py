import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status

from app.repositories.user_repo import UserRepository
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.schemas.auth import TokenResponse
from app.core.security import (
    create_access_token,
    hash_token,
    generate_refresh_token,
    verify_password,
    get_password_hash,
)
from app.core.config import settings
from app.models.models import RefreshToken, User


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def _issue_token_pair(
        self,
        user: User,
        family_id: Optional[uuid.UUID] = None,
        device_info: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> TokenResponse:
        # Access token (short-lived)
        access_token = create_access_token(subject=user.id)

        # Refresh token
        raw_refresh = generate_refresh_token()
        t_hash = hash_token(raw_refresh)
        fam_id = family_id or uuid.uuid4()
        expires = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS)

        refresh_record = RefreshToken(
            token_hash=t_hash,
            user_id=user.id,
            family_id=fam_id,
            is_revoked=False,
            device_info=device_info,
            ip_address=ip_address,
            expires_at=expires
        )
        self.db.add(refresh_record)
        await self.db.commit()

        user_response = UserResponse.from_user(user)
        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh,
            expires_in=settings.JWT_ACCESS_EXPIRE_MINUTES * 60,
            user=user_response
        )

    async def register_user(
        self, user_in: UserCreate, device_info: Optional[str] = None, ip_address: Optional[str] = None
    ) -> TokenResponse:
        existing_user = await self.user_repo.get_by_email(user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address already exists."
            )

        hashed_pwd = get_password_hash(user_in.password) if user_in.password else None
        user = await self.user_repo.create(
            email=user_in.email,
            full_name=user_in.full_name,
            hashed_password=hashed_pwd
        )

        return await self._issue_token_pair(user, device_info=device_info, ip_address=ip_address)

    async def login_user(
        self, credentials: UserLogin, device_info: Optional[str] = None, ip_address: Optional[str] = None
    ) -> TokenResponse:
        user = await self.user_repo.get_by_email(credentials.email)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password."
            )

        if not user.hashed_password or not verify_password(credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password."
            )

        return await self._issue_token_pair(user, device_info=device_info, ip_address=ip_address)

    async def refresh_access_token(
        self, raw_refresh_token: str, device_info: Optional[str] = None, ip_address: Optional[str] = None
    ) -> TokenResponse:
        t_hash = hash_token(raw_refresh_token)
        # Row-level lock ensures sequential handling of concurrent refresh requests
        query = select(RefreshToken).where(RefreshToken.token_hash == t_hash).with_for_update()
        result = await self.db.execute(query)
        token_record = result.scalar_one_or_none()

        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token."
            )

        now = datetime.now(timezone.utc)

        # TOKEN REUSE DETECTION & MULTI-TAB RACE HANDLING
        if token_record.is_revoked:
            # If token was explicitly revoked via family compromise or logout, refuse unconditionally
            if token_record.device_info and token_record.device_info.startswith("REVOKED_"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked. Session terminated."
                )

            # Check for benign multi-tab concurrent refresh within 3-second grace window
            revocation_time = token_record.updated_at
            if revocation_time:
                if revocation_time.tzinfo is None:
                    revocation_time = revocation_time.replace(tzinfo=timezone.utc)
                age = (now - revocation_time).total_seconds()
                if age <= 3.0:
                    # Concurrently refreshed within 3 seconds: Return valid access token without family revocation
                    user = await self.user_repo.get_by_id(token_record.user_id)
                    if user and user.is_active:
                        access_token = create_access_token(subject=str(user.id))
                        user_resp = UserResponse.from_user(user)
                        return TokenResponse(
                            access_token=access_token,
                            refresh_token=None,
                            token_type="bearer",
                            expires_in=settings.JWT_ACCESS_EXPIRE_MINUTES * 60,
                            user=user_resp
                        )

            # Replay outside grace period: Revoke entire token family to protect against compromised credentials
            revoke_query = select(RefreshToken).where(RefreshToken.family_id == token_record.family_id).with_for_update()
            family_tokens = (await self.db.execute(revoke_query)).scalars().all()
            for t in family_tokens:
                t.is_revoked = True
                t.device_info = f"REVOKED_COMPROMISED:{t.device_info or ''}"[:255]
            await self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token reuse detected. Session terminated for security."
            )

        # Check expiration
        exp = token_record.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp < now:
            token_record.is_revoked = True
            await self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired. Please log in again."
            )

        # Mark current token revoked (rotated) with updated timestamp
        token_record.is_revoked = True
        token_record.updated_at = now
        await self.db.commit()

        # Load user
        user = await self.user_repo.get_by_id(token_record.user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive or not found."
            )

        # Issue new rotated token pair within same family
        return await self._issue_token_pair(
            user,
            family_id=token_record.family_id,
            device_info=device_info or token_record.device_info,
            ip_address=ip_address or token_record.ip_address
        )

    async def logout_user(self, raw_refresh_token: Optional[str] = None, user_id: Optional[uuid.UUID] = None) -> bool:
        if raw_refresh_token:
            t_hash = hash_token(raw_refresh_token)
            query = select(RefreshToken).where(RefreshToken.token_hash == t_hash)
            result = await self.db.execute(query)
            token = result.scalar_one_or_none()
            if token:
                token.is_revoked = True
                token.device_info = f"REVOKED_LOGOUT:{token.device_info or ''}"[:255]
                await self.db.commit()
                return True
        elif user_id:
            query = select(RefreshToken).where(RefreshToken.user_id == user_id, RefreshToken.is_revoked == False)
            tokens = (await self.db.execute(query)).scalars().all()
            for t in tokens:
                t.is_revoked = True
                t.device_info = f"REVOKED_LOGOUT:{t.device_info or ''}"[:255]
            await self.db.commit()
            return True
        return False

    async def logout(self, raw_refresh_token: Optional[str] = None, user_id: Optional[uuid.UUID] = None) -> bool:
        return await self.logout_user(raw_refresh_token=raw_refresh_token, user_id=user_id)

    async def get_current_user_profile(self, user_id_str: str) -> UserResponse:
        from uuid import UUID
        user = await self.user_repo.get_by_id(UUID(user_id_str))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found."
            )
        return UserResponse.from_user(user)

