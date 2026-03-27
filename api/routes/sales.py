from datetime import date
from decimal import Decimal
from pydantic import BaseModel


class SaleModel(BaseModel):
    doc_no: str
    sale_date: date
    partner_inn: str
    item_code: str
    qty: Decimal
    price: Decimal
    amount: Decimal