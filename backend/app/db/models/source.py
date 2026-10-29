from sqlalchemy import Integer, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.database import Base


class SourceRecord(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id"),
        nullable=False
    )

    source_url: Mapped[str] = mapped_column(
        Text, nullable=False
    )

    source_type: Mapped[str | None] = mapped_column(String(50))

    product = relationship(
        "ProductRecord", back_populates="sources"
    )
