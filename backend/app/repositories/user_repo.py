from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.models import User, UserSettings, Credit, CreditTransactionType, AuthProvider


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        query = select(User).where(User.id == user_id).options(selectinload(User.settings))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        query = select(User).where(User.email == email.lower().strip()).options(selectinload(User.settings))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create(self, email: str, full_name: str, auth_provider: AuthProvider = AuthProvider.email) -> User:
        user = User(
            email=email.lower().strip(),
            full_name=full_name,
            auth_provider=auth_provider,
            is_active=True,
            is_verified=True
        )
        self.db.add(user)
        await self.db.flush()

        # Create default User Settings
        settings = UserSettings(user_id=user.id)
        self.db.add(settings)

        # Grant 100 Signup Bonus Credits
        credit = Credit(
            user_id=user.id,
            amount=100,
            transaction_type=CreditTransactionType.bonus,
            description="Welcome Sign-up Bonus Credits",
            balance_after=100
        )
        self.db.add(credit)

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update(self, user: User) -> User:
        await self.db.commit()
        await self.db.refresh(user)
        return user
