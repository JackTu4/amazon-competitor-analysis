from sqlalchemy import Integer, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.database import Base


class ReportRecord(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    task_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.task_id"),
        nullable=False,
        unique=True
    )

    markdown: Mapped[str] = mapped_column(
        Text, nullable=False
    )

    file_path: Mapped[str | None] = mapped_column(Text)

    project = relationship(
        "Project", back_populates="report"
    )
