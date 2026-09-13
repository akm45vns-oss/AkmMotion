from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.schemas.auth import TokenResponse
from app.core.security import create_access_token, get_password_hash
from app.core.config import settings


class AuthService:
    def __init__(self, db: AsyncSession):
        self.user_repo = UserRepository(db)

    async def register_user(self, user_in: UserCreate) -> TokenResponse:
        existing_user = await self.user_repo.get_by_email(user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address already exists."
            )

        user = await self.user_repo.create(
            email=user_in.email,
            full_name=user_in.full_name
        )

        access_token = create_access_token(subject=user.id)
        user_response = UserResponse.from_user(user)

        return TokenResponse(
            access_token=access_token,
            expires_in=settings.JWT_EXPIRE_MINUTES * 60,
            user=user_response
        )

    async def login_user(self, credentials: UserLogin) -> TokenResponse:
        user = await self.user_repo.get_by_email(credentials.email)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or account is inactive."
            )

        access_token = create_access_token(subject=user.id)
        user_response = UserResponse.from_user(user)

        return TokenResponse(
            access_token=access_token,
            expires_in=settings.JWT_EXPIRE_MINUTES * 60,
            user=user_response
        )

    async def get_current_user_profile(self, user_id_str: str) -> UserResponse:
        from uuid import UUID
        user = await self.user_repo.get_by_id(UUID(user_id_str))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found."
            )
        return UserResponse.from_user(user)
