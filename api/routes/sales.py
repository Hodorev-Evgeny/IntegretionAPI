from decimal import Decimal
from datetime import date

from sqlalchemy import String, Date, Numeric, ForeignKey, CheckConstraint, Computed
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class Sales(Base):
    __tablename__ = 'sales'

    doc_no: Mapped[str] = mapped_column(String(50), primary_key=True)
    sale_date: Mapped[date] = mapped_column(Date, nullable=False)

    partner_inn: Mapped[str] = mapped_column(
        String(12),
        ForeignKey('partners.inn'),
        nullable=False
    )

    item_code: Mapped[str] = mapped_column(
        String(10),
        ForeignKey('item.code'),
        nullable=False
    )

    qty: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        Computed("qty * price", persisted=True)
    )

    __table_args__ = (
        CheckConstraint("qty > 0", name='chk_sales_qty'),
        CheckConstraint("price > 0", name='chk_sales_price'),
    )