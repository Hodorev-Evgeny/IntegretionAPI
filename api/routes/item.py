from pydantic import BaseModel


class ItemModel(BaseModel):
    code: str
    name: str
    uom: str
    vat_rate: int
