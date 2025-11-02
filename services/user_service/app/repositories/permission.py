from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from app.repositories.interfaces.permission import IPermissionRepository
from app.models.permission import Permission
from app.schemas.permission import PermissionCreate, PermissionUpdateInDB
from app.core.exceptions import RepositoryError, EntityAlreadyExists


class PermissionRepository(IPermissionRepository):

    async def create(self, db: AsyncSession, payload: PermissionCreate) -> Permission:

        """Create a new permission."""

        try:
            new_permission = Permission(
                name = payload.name, 
                description = payload.description
            )

            db.add(new_permission)
            await db.flush()
            await db.refresh(new_permission)
            
            return new_permission
        
        except Exception as e:
            raise RepositoryError("Error creating permission") from e

    async def read_by_id(self, db: AsyncSession, permission_id: UUID) -> Optional[Permission]:

        '''Get a permission by its ID.'''

        try:
            result = await db.execute(
                select(Permission)
                .where(Permission.id == permission_id)
            )

            return result.scalar_one_or_none()
        
        except Exception as e:
            raise RepositoryError(f"Error reading permission by ID: {str(e)}") from e
    
    async def read_with_filters(self,
                                db: AsyncSession, 
                                name: Optional[List[str]] = None,
                                description: Optional[str] = None,
                                skip: int = 0, 
                                limit: int = 100
                                ) -> List[Permission]:
        
        """Get permissions with filters."""
        
        try:
            query = select(Permission)
            
            if name is not None:
                query = query.where(Permission.name.in_(name))

            if description is not None:
                query = query.where(Permission.description.ilike(f"%{description}%"))
            
            query = query.offset(skip).limit(limit)
            
            result = await db.execute(query)

            return result.scalars().all()

        except Exception as e:
           raise RepositoryError(f"Error reading permission with filters: {str(e)}") from e

    async def read_by_names(self, db: AsyncSession, names: List[str]) -> List[Permission]:

        '''Retrieve permissions matching provided names list'''

        try:
            query = select(Permission).where(Permission.name.in_(names))

            result = await db.execute(query)

            return result.scalars().all()
        
        except Exception as e:
            raise RepositoryError(f"Error reading permissions by names: {str(e)}") from e

    async def update(self, db: AsyncSession, permission_id: UUID, payload: PermissionUpdateInDB) -> Permission:

        try:
            db_permission = await self.read_by_id(db, permission_id)

            if hasattr(payload, "model_dump"):
                data = payload.model_dump(exclude_unset=True, exclude_none=True)
            else:
                data = dict(payload or {})

            for key, value in data.items():
                setattr(db_permission, key, value)

            await db.flush()
            await db.refresh(db_permission)

            return db_permission

        except Exception as e:
            raise RepositoryError(f"Error updating permission: {str(e)}") from e

    async def delete(self, db: AsyncSession, permission_id: UUID) -> None:

        """Delete a permission by ID."""

        try:
            await db.execute(delete(Permission).where(Permission.id == permission_id))
            await db.flush()
            
        except Exception as e:
            raise RepositoryError(f"Error deleting permission: {str(e)}") from e


