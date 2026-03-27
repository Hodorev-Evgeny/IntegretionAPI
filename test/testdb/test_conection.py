import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
from api.models.db_session import get_settings_from_engine


async def test_connection(engine: AsyncEngine):
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        print(result.scalar())


async def main():
    engine = get_settings_from_engine()
    await test_connection(engine)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())