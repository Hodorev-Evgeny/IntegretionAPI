from sqlalchemy import String, Integer, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class Item(Base):
    __tablename__ = 'item'

    code: Mapped[str] = mapped_column(String(10), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    uom: Mapped[str] = mapped_column(String(10), nullable=False)
    vat_rate: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint("uom IN ('l', 'с', 'шт', 'кг')", name='chk_item_uom'),
        CheckConstraint("vat_rate IN (0, 10, 20)", name='chk_item_vat_rate'),
    )