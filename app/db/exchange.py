from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ExchangeOperation(Base):
    __tablename__ = "exchange_operations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    entity: Mapped[str] = mapped_column(String(50), nullable=False)
    target: Mapped[str] = mapped_column(String(20), nullable=False)
    filename: Mapped[str | None] = mapped_column(String(255), nullable=True)

    status: Mapped[str] = mapped_column(String(50), nullable=False, default="received")

    total_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    valid_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    invalid_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sent_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    target_status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_response: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    rows: Mapped[list["ExchangeFileRow"]] = relationship(
        back_populates="operation",
        cascade="all, delete-orphan",
    )


class ExchangeFileRow(Base):
    __tablename__ = "exchange_file_rows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    operation_id: Mapped[int] = mapped_column(
        ForeignKey("exchange_operations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)

    raw_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    validated_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    operation: Mapped["ExchangeOperation"] = relationship(
        back_populates="rows",
    )