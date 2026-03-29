import csv
import io

import uvicorn
from datetime import datetime
from decimal import Decimal
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import sessionmaker

from api.models.item import Item
from api.models.partners import Partners
from api.models.sales import Sales

from deps import *


app = FastAPI()


@app.get("/test_connection")
async def test_connection():
    return {"status": "ok"}


@app.post("/upload/item")
async def create_item(
        session: SessionDep,
        upitem: UploadFile = File(...),

):

    if not upitem.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Not a csv")

    content = await upitem.read()
    text = content.decode("utf-8")
    csvfile = io.StringIO(text)
    reader = csv.DictReader(csvfile)

    cach = []
    for row in reader:
        item = Item(
            code=row["code"],
            name=row["name"],
            uom=row["uom"],
            vat_rate = int(row["vat_rate"].strip()),
        )
        cach.append(item)

    session.add_all(cach)
    await session.commit()

    return {"status": "ok", "message": "Item add"}

@app.post("/upload/partners")
async def create_item(
        session: SessionDep,
        uppartners: UploadFile = File(...),
):
    if not uppartners.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Not a csv")

    content = await uppartners.read()
    text = content.decode("utf-8")
    csvfile = io.StringIO(text)
    reader = csv.DictReader(csvfile)
    cach = []
    for row in reader:
        partner = Partners(
            name=row["name"],
            inn=row["inn"],
            kpp=row["kpp"],
        )
        cach.append(partner)
    session.add_all(cach)
    await session.commit()

    return {"status": "ok", "message": "Partners add"}

@app.post("/upload/sales")
async def create_item(
        session: SessionDep,
        upsales: UploadFile = File(...),
):
    if not upsales.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Not a csv")
    content = await upsales.read()
    text = content.decode("utf-8")
    csvfile = io.StringIO(text)
    reader = csv.DictReader(csvfile)

    cach = []
    for row in reader:
        sale = Sales(
            doc_no=row["doc_no"],
            sale_date=datetime.strptime(row["sale_date"], "%Y-%m-%d").date(),
            partner_inn=row["partner_inn"],
            item_code=row["item_code"],
            qty=Decimal(row["qty"]),
            price=Decimal(row["price"]),
        )
        cach.append(sale)
    session.add_all(cach)
    await session.commit()

    return {"status": "ok", "message": "Sales add"}

if __name__ == "__main__":
    uvicorn.run(app, port=8000)