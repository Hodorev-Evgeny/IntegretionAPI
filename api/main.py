import csv
import io

import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import sessionmaker

from api.models.item import Item
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

    return {"status": "ok", "message": "Item created"}



if __name__ == "__main__":
    uvicorn.run(app, port=8000)