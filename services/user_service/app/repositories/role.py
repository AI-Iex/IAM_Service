from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, delete, update
from app.schemas.role import RoleCreate, RoleRead, RoleUpdate
from app.repositories.interfaces.role import IRoleRepository
from app.models.role import Role
from app.models.permission import Permission
from typing import Optional, List
from app.core.exceptions import EntityAlreadyExists, RepositoryError, NotFoundError
from sqlalchemy.exc import IntegrityError


class RoleRepository(IRoleRepository):
    
    async def create(self, db: AsyncSession, role: RoleCreate) -> Role:

        """Create a new role."""

        try:
            new_role = Role(
                name=role.name,
                description=role.description
            )

            db.add(new_role)
            await db.flush()
            await db.refresh(new_role)

            return new_role
        
        except Exception as e:
            raise RepositoryError("Error creating role") from e


    async def read_by_id(self, db: AsyncSession, role_id: UUID) -> Optional[Role]:

        """Get a role by its ID."""

        try:
            result = await db.execute(
                select(Role)
                .where(Role.id == role_id)
                .options(selectinload(Role.permissions))
            )

            return result.scalar_one_or_none()
        
        except Exception as e:
            raise RepositoryError(f"Error reading role by ID: {str(e)}") from e


    async def read_with_filters(self, 
                                db: AsyncSession,
                                name: Optional[str] = None, 
                                description: Optional[str] = None,
                                skip: int = 0, 
                                limit: int = 100
                            ) -> List[Role]:
        
        """Get roles with filters."""

        try:
            query = select(Role).options(selectinload(Role.permissions))
            
            if name is not None:
                query = query.where(Role.name.ilike(f"%{name}%"))
            
            if description is not None:
                query = query.where(Role.description.ilike(f"%{description}%"))
            
            query = query.offset(skip).limit(limit)
            
            result = await db.execute(query)

            return result.scalars().all()
        
        except Exception as e:
            raise RepositoryError(f"Error reading role with filters: {str(e)}") from e
  
   
    async def update(self, db: AsyncSession, role_id: UUID, role: RoleUpdate) -> Role:

        """Update an existing Role entity with provided data."""

        try:
            # 1. First get the Role entity from database
            db_role = await self.read_by_id(db, role_id)
            
            # 2. Transform the RoleUpdate schema into a dict, excluding id
            update_data = role.model_dump(exclude_unset = True, exclude = {'id'})

            # 3. Separate permissions from other fields
            permissions_data = update_data.pop("permissions", None)

            # 4. Update simple fields of the model
            for key, value in update_data.items():
                setattr(db_role, key, value)

            # 5. Update permissions if provided
            if permissions_data is not None:
                result = await db.execute(
                    select(Permission).where(Permission.name.in_(permissions_data))
                )
                permissions = result.scalars().all()
                db_role.permissions = permissions

            await db.flush()
            await db.refresh(db_role)

            return db_role

        except Exception as e:
            raise RepositoryError(f"Error updating role: {str(e)}") from e

   
    async def delete(self, db: AsyncSession, role_id: UUID) -> None:

        """Delete a role instance from the DB."""
        
        try:
            await db.execute(delete(Role).where(Role.id == role_id))
            await db.flush()
        
        except Exception as e:
            raise RepositoryError(f"Error deleting role: {str(e)}") from e

