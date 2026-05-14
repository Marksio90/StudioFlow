import asyncio

from sqlalchemy import text

from app.db.session import engine


async def seed() -> None:
    async with engine.begin() as conn:
        await conn.execute(text("INSERT INTO organizations (id, name) VALUES (gen_random_uuid(), 'Demo Org') ON CONFLICT DO NOTHING"))


if __name__ == "__main__":
    asyncio.run(seed())
