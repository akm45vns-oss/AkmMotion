from datetime import datetime, timezone
import uuid
from sqlalchemy import DateTime, Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, declared_attr


def utc_now():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    @declared_attr.directive
    def __tablename__(cls) -> str:
        # Converts CamelCase class name to snake_case table name
        name = cls.__name__
        return "".join(["_" + c.lower() if c.isupper() else c for c in name]).lstrip("_")
