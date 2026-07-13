"""SQLAlchemy ORM models."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CnpjCache(Base):
    """Cache table storing raw BrasilAPI CNPJ responses."""

    __tablename__ = "cnpj_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cnpj: Mapped[str] = mapped_column(
        String(14), unique=True, index=True, nullable=False
    )
    data: Mapped[dict] = mapped_column(JSON, nullable=False)
    consulted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    source: Mapped[str] = mapped_column(String(50), default="brasilapi", nullable=False)

    def __repr__(self) -> str:
        return f"<CnpjCache cnpj={self.cnpj!r} consulted_at={self.consulted_at}>"
