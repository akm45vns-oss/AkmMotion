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


@router.post("/logout")
async def logout(current_user_id: str = Depends(get_current_user_id)):
    return {"message": "Successfully logged out"}


@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest):
    return {"message": f"Password reset instructions sent to {req.email} if account exists."}
