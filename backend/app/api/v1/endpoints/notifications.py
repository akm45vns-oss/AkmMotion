from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel, ConfigDict
from app.core.dependencies import get_db, get_current_user_id
from app.models.models import Notification, NotificationType


class NotificationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: NotificationType
    title: str
    message: str
    is_read: bool


router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=List[NotificationSchema])
async def list_notifications(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(Notification)
        .where(Notification.user_id == UUID(current_user_id))
        .order_by(Notification.created_at.desc())
        .limit(10)
    )
    res = await db.execute(query)
    items = list(res.scalars().all())

    if not items:
        # Default welcome notification
        return [
            NotificationSchema(
                id=UUID("00000000-0000-0000-0000-000000000001"),
                type=NotificationType.render_complete,
                title="Welcome to AkmMotion Studio!",
                message="You have received 100 free AI video generation credits.",
                is_read=False
            )
        ]

    return [NotificationSchema.model_validate(n) for n in items]
