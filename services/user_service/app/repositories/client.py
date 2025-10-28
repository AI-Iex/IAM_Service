from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.client import Client


class ClientRepository:
    async def get_by_client_id(self, db: AsyncSession, client_id: str):
        q = select(Client).where(Client.client_id == client_id)
        res = await db.execute(q)
        return res.scalars().first()

    async def create_client(self, db: AsyncSession, client_id: str, hashed_secret: str, name: str | None = None, scopes: str | None = None):
        c = Client(client_id=client_id, hashed_secret=hashed_secret, name=name, scopes=scopes)
        db.add(c)
        await db.flush()
        await db.refresh(c)
        return c
