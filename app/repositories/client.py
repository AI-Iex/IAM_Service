from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.client import Client
from app.models.client_permission import ClientPermission
from app.schemas.client import ClientUpdate, ClientCreateInDB
from typing import Optional, List
from uuid import UUID
from app.core.exceptions import RepositoryError
from app.repositories.interfaces.client import IClientRepository


class ClientRepository(IClientRepository):

# region CREATE

    async def create(self, db: AsyncSession, client: ClientCreateInDB) -> Client:
        try:
            new_client = Client(
                name = client.name,
                is_active = client.is_active,
                hashed_secret = client.secret_hashed,
                client_id = client.client_id
            )

            db.add(new_client)
            await db.flush()
            await db.refresh(new_client)
            return new_client

        except Exception as e:
            raise RepositoryError("Error creating client: " + str(e)) from e

# endregion CREATE

# region READ

    async def read_by_id(self, db: AsyncSession, client_id: UUID) -> Optional[Client]:

        try:
            result = await db.execute(
                select(Client)
                .where(Client.id == client_id)
                .options(selectinload(Client.permissions))
            )

            return result.scalar_one_or_none()
        
        except Exception as e:
            raise RepositoryError(f"Error reading client by ID: {str(e)}") from e

    async def read_by_clientid(self, db: AsyncSession, clientid: UUID) -> Optional[Client]:

        try:
            result = await db.execute(
                select(Client)
                .where(Client.client_id == clientid)
                .options(selectinload(Client.permissions))
            )

            return result.scalar_one_or_none()
        
        except Exception as e:
            raise RepositoryError(f"Error reading client by clientID: {str(e)}") from e

    async def read_with_filters(
        self, 
        db: AsyncSession, 
        name: Optional[str] = None, 
        is_active: Optional[bool] = None, 
        skip: int = 0,
        limit: int = 100
    ) -> List[Client]:

        try:
            query = select(Client).options(selectinload(Client.permissions))
            
            if name is not None:
                query = query.where(Client.name.ilike(f"%{name}%"))
            
            if is_active is not None:
                query = query.where(Client.is_active == is_active)
            
            query = query.offset(skip).limit(limit)
            
            result = await db.execute(query)

            return result.scalars().all()
        
        except Exception as e:
            raise RepositoryError(f"Error reading client with filters: {str(e)}") from e
  
# endregion READ

# region UPDATE

    async def update(self, db: AsyncSession, client_id: UUID, update_data: ClientUpdate) -> Client:

        try:

            client = await self.read_by_id(db, client_id)

            if hasattr(update_data, "model_dump"):
                data = update_data.model_dump(exclude_unset = True, exclude_none = True)
            else:
                data = dict(update_data or {})

            for key, value in data.items():
                setattr(client, key, value)

            await db.flush()
            await db.refresh(client)
            return client

        except Exception as e:
            raise RepositoryError(f"Error updating client: {str(e)}") from e

    async def assign_permission(self, db: AsyncSession, client_id: UUID, permission_id: UUID) -> Client:
       
        try:
            cp = ClientPermission(client_id = client_id, permission_id = permission_id)
            db.add(cp)
            await db.flush()

            client = await self.read_by_id(db, client_id)
            await db.refresh(client)
            return client
        
        except Exception as e:
            raise RepositoryError(f"Error adding permission to client: {str(e)}") from e

    async def assign_list_permissions(self, db: AsyncSession, client_id: UUID, permission_ids: List[UUID]) -> Client:
        
        ''' Assign a list of permissions to a client removing existing ones. '''

        try:

            db_client = await self.read_by_id(db, client_id)

            # remove existing client permissions
            await db.execute(delete(ClientPermission).where(ClientPermission.client_id == client_id))

            # add new ones
            if permission_ids:
                for pid in permission_ids:
                    cp = ClientPermission(client_id=client_id, permission_id=pid)
                    db.add(cp)

            await db.flush()
            await db.refresh(db_client)

            return db_client

        except Exception as e:
            raise RepositoryError(f"Error adding permissions to a client: {str(e)}") from e

    async def remove_permission(self, db: AsyncSession, client_id: UUID, permission_id: UUID) -> Client:
       
        try:
            db_client = await self.read_by_id(db, client_id)

            await db.execute(delete(ClientPermission).where(
                ClientPermission.client_id == client_id,
                ClientPermission.permission_id == permission_id
            ))

            await db.flush()
            await db.refresh(db_client)

            return db_client

        except Exception as e:
            raise RepositoryError(f"Error removing permission from client: {str(e)}") from e


# endregion UPDATE

#region CHECK

    async def has_permission(self, db: AsyncSession, client_id: UUID, permission_id: UUID) -> bool:
        
        try:
            result = await db.execute(
                select(ClientPermission).where(
                    ClientPermission.client_id == client_id,
                    ClientPermission.permission_id == permission_id
                )
            )

            return result.first() is not None
        
        except Exception as e:
            raise RepositoryError(f"Error checking client permission existence: {str(e)}") from e
        
#endregion CHECK

#region DELETE

    async def delete(self, db: AsyncSession, client_id: UUID) -> None:
        
        try:
            await db.execute(delete(Client).where(Client.id == client_id))
            await db.flush()
        
        except Exception as e:
            raise RepositoryError(f"Error deleting client: {str(e)}") from e

#endregion DELETE





