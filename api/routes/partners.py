from sqlalchemy import String, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class Partners(Base):
    __tablename__ = 'partners'

    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    inn: Mapped[str] = mapped_column(String(12), primary_key=True)
    kpp: Mapped[str] = mapped_column(String(9), nullable=False)

    __table_args__ = (
        CheckConstraint(r"inn ~ '^[0-9]{10}$|^[0-9]{12}$'", name='chk_partners_inn'),
        CheckConstraint(r"kpp ~ '^[0-9]{9}$'", name='chk_partners_kpp'),
    )