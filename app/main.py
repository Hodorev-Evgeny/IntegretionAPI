from fastapi import FastAPI

from app.api.router import api_router
from app.core.middleware import request_id_middleware
from app.db.db_session import create_tables


app = FastAPI(
    title="1C UNF <-> 1C BP Integration API",
    version="1.0.0",
)


@app.on_event("startup")
async def startup():
    await create_tables()


app.middleware("http")(request_id_middleware)

app.include_router(api_router)


@app.get("/test_connection")
async def test_connection():
    return {
        "status": "ok",
        "message": "Connection successful",
    }