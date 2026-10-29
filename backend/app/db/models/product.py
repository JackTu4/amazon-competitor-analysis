from decimal import Decimal

from sqlalchemy import (
    Integer,
    String,
    Text,
    Numeric,
    Float,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.database import Base


class ProductRecord(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    task_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.task_id"),
        nullable=False
    )

    role: Mapped[str] = mapped_column(
        String(20), nullable=False
    )

    name: Mapped[str | None] = mapped_column(String(500))
    title: Mapped[str | None] = mapped_column(Text)
    asin: Mapped[str | None] = mapped_column(String(20))
    brand: Mapped[str | None] = mapped_column(String(200))

    price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2)
    )

    currency: Mapped[str | None] = mapped_column(String(10))
    rating: Mapped[float | None] = mapped_column(Float)
    reviews: Mapped[int | None] = mapped_column(Integer)

    project = relationship(
        "Project", back_populates="products"
    )

    sources = relationship(
        "SourceRecord", back_populates="product"
    )
