from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.database import Base


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Project(Base):
    __tablename__ = "projects"

    task_id: Mapped[str] = mapped_column(
        String(36), primary_key=True
    )

    target_product: Mapped[str] = mapped_column(
        String(500), nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )

    result: Mapped[str | None] = mapped_column(Text)
    error: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )

    products = relationship(
        "ProductRecord", back_populates="project"
    )

    report = relationship(
        "ReportRecord",
        back_populates="project",
        uselist=False
    )
