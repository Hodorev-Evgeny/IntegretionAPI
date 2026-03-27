from fastapi import Depends
from typing import Annotated
from api.models.db_session import get_session
from sqlalchemy.ext.asyncio import AsyncSession


async def session_depends():
    async with Session() as s:
        yield s

Session = get_session()

SessionDep = Annotated[AsyncSession, Depends(session_depends)]