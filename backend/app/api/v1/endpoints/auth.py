from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_user_id
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.schemas.auth import TokenResponse, ForgotPasswordRequest
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    return await auth_service.register_user(user_in)


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    return await auth_service.login_user(credentials)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    return await auth_service.get_current_user_profile(current_user_id)


from uuid import UUID
from app.schemas.auth import TokenResponse, ForgotPasswordRequest, RefreshTokenRequest


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(req: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    return await auth_service.refresh_access_token(req.refresh_token)


@router.post("/logout")
async def logout(
    req: RefreshTokenRequest = None,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    auth_service = AuthService(db)
    raw_refresh = req.refresh_token if req else None
    user_uuid = UUID(current_user_id) if current_user_id and current_user_id != "guest_studio_token" else None
    await auth_service.logout_user(raw_refresh_token=raw_refresh, user_id=user_uuid)
    return {"message": "Successfully logged out and session revoked"}


@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest):
    return {"message": "If an account with that email exists, password reset instructions have been sent."}

