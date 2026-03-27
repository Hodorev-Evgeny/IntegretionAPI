from pydantic import BaseModel


class PartnerModel(BaseModel):
    name: str
    inn: str
    kpp: str
