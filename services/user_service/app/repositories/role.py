from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, delete, update
from app.schemas.role import RoleCreate, RoleRead, RoleUpdate, RoleUpdateInDB
from app.repositories.interfaces.role import IRoleRepository
from app.models.role import Role
from typing import Optional, List
from uuid import UUID
from app.models.role_permission import RolePermission
from app.core.exceptions import EntityAlreadyExists, RepositoryError, NotFoundError
from sqlalchemy.exc import IntegrityError
from app.models.user_role import UserRole
from sqlalchemy.exc import IntegrityError


class RoleRepository(IRoleRepository):
    

# region CREATE

    async def create(self, db: AsyncSession, role: RoleCreate) -> Role:

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
            raise RepositoryError("Error creating role: " + str(e)) from e

# endregion CREATE

# region READ

    async def read_by_id(self, db: AsyncSession, role_id: UUID) -> Optional[Role]:

        try:
            result = await db.execute(
                select(Role)
                .where(Role.id == role_id)
                .options(selectinload(Role.permissions))
            )

            return result.scalar_one_or_none()
        
        except Exception as e:
            raise RepositoryError(f"Error reading role by ID: {str(e)}") from e


    async def read_with_filters(
            self, 
            db: AsyncSession,
            name: Optional[str] = None, 
            description: Optional[str] = None,
            skip: int = 0, 
            limit: int = 100
    ) -> List[Role]:

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
  

    async def read_by_names(self, db: AsyncSession, names: List[str]) -> List[Role]:

        try:
            query = select(Role).where(Role.name.in_(names)).options(selectinload(Role.permissions))
            
            result = await db.execute(query)
            
            return result.scalars().all()
        
        except Exception as e:
            raise RepositoryError(f"Error reading roles by names: {str(e)}") from e
   

    async def read_by_user_id_with_permissions(self, db: AsyncSession, user_id: UUID) -> List[Role]:
       
        try:
            ur_table = UserRole.__table__
            query = select(Role).join(ur_table, ur_table.c.role_id == Role.id).where(ur_table.c.user_id == user_id).options(selectinload(Role.permissions))
            result = await db.execute(query)
            
            return result.scalars().all()
        
        except Exception as e:
            raise RepositoryError(f"Error reading roles for user {user_id}: {str(e)}") from e

# endregion READ

# region UPDATE

    async def update(self, db: AsyncSession, role_id: UUID, update_data: RoleUpdateInDB) -> Role:

        try:
            
            role = await self.read_by_id(db, role_id)
           
            if hasattr(update_data, "model_dump"):
                data = update_data.model_dump(exclude_unset=True, exclude_none=True)
            else:
                data = dict(update_data or {})

            for key, value in data.items():
                setattr(role, key, value)

            await db.flush()
            await db.refresh(role)
            return role
        
        except Exception as e:
            raise RepositoryError(f"Error updating role: {str(e)}") from e


    async def add_permission(self, db: AsyncSession, role_id: UUID, permission_id: UUID) -> Role:
       
        try:
            rp = RolePermission(role_id=role_id, permission_id=permission_id)
            db.add(rp)
            await db.flush()

            role = await self.read_by_id(db, role_id)
            await db.refresh(role)
            return role
        
        except Exception as e:
            raise RepositoryError(f"Error adding permission to role: {str(e)}") from e


    async def set_permissions(self, db: AsyncSession, role_id: UUID, permission_ids: List[UUID]) -> Role:

        try:
            
            db_role = await self.read_by_id(db, role_id)

            # remove existing role permissions
            await db.execute(delete(RolePermission).where(RolePermission.role_id == role_id))

            # add new ones
            if permission_ids:
                for pid in permission_ids:
                    rp = RolePermission(role_id=role_id, permission_id=pid)
                    db.add(rp)

            await db.flush()
            await db.refresh(db_role)

            return db_role
        
        except Exception as e:
            raise RepositoryError(f"Error setting permissions for role: {str(e)}") from e


    async def remove_permission(self, db: AsyncSession, role_id: UUID, permission_id: UUID) -> Role:
       
        try:
            role = await self.read_by_id(db, role_id)

            await db.execute(delete(RolePermission).where(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == permission_id
            ))

            await db.flush()
            await db.refresh(role)

            return role
        
        except Exception as e:
            raise RepositoryError(f"Error removing permission from role: {str(e)}") from e

# endregion UPDATE

#region CHECK

    async def has_permission(self, db: AsyncSession, role_id: UUID, permission_id: UUID) -> bool:
        
        try:
            result = await db.execute(
                select(RolePermission).where(
                    RolePermission.role_id == role_id,
                    RolePermission.permission_id == permission_id
                )
            )

            return result.first() is not None
        
        except Exception as e:
            raise RepositoryError(f"Error checking role permission existence: {str(e)}") from e
        
#endregion CHECK

#region DELETE

    async def delete(self, db: AsyncSession, role_id: UUID) -> None:
        
        try:
            await db.execute(delete(Role).where(Role.id == role_id))
            await db.flush()
        
        except Exception as e:
            raise RepositoryError(f"Error deleting role: {str(e)}") from e

#endregion DELETE
