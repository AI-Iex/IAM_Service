from datetime import datetime, timedelta, timezone
from typing import Optional, List
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, delete, update
from app.models.user import User
from app.schemas.user import UserCreateInDB, UserUpdateInDB
from app.core.exceptions import EntityAlreadyExists, RepositoryError
from app.repositories.interfaces.user import IUserRepository
from uuid import UUID
from app.models.user_role import user_roles
from sqlalchemy import select
from app.core.exceptions import RepositoryError

class UserRepository(IUserRepository):

    # region CREATE

    async def create(self, db: AsyncSession, dto: UserCreateInDB) -> User:
        try:
            user = User(
                email=dto.email,
                full_name=dto.full_name,
                hashed_password=dto.hashed_password,
                is_active=dto.is_active,
                is_superuser=dto.is_superuser,
                require_password_change=dto.require_password_change
            )

            db.add(user)
            await db.flush()
            await db.refresh(user)
            return user
        
        except IntegrityError as e:
            if "unique" in str(e).lower() or "duplicate" in str(e).lower():
                raise EntityAlreadyExists("User with that email already exists") from e
            raise RepositoryError("Database integrity error") from e
        
        except Exception as e:
            raise RepositoryError("Unexpected database error") from e

    # endregion CREATE

    # region READ

    async def get_with_filters(
        self,
        db: AsyncSession,
        name: Optional[str] = None,
        email: Optional[List[str]] = None,
        active: Optional[bool] = None,
        is_superuser: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        
        try:

            query = select(User)

            if name is not None:
                query = query.where(User.full_name.ilike(f"%{name}%"))

            if email is not None:
                query = query.where(User.email.in_(email))

            if active is not None:
                query = query.where(User.is_active == active)

            if is_superuser is not None:
                query = query.where(User.is_superuser == is_superuser)

            query = query.offset(skip).limit(limit)

            result = await db.execute(query)
            return result.scalars().all()
        
        except Exception as e:
            raise RepositoryError(f"Error retrieving users with filters: {str(e)}") from e

    async def get_by_id(self, db: AsyncSession, user_id: UUID) -> Optional[User]:
        
        try:

            result = await db.execute(
                select(User)
                .where(User.id == user_id)
            )
            return result.scalar_one_or_none()
        
        except Exception as e:
            raise RepositoryError(f"Error retrieving user by ID: {str(e)}") from e

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        
        try:

            result = await db.execute(
                select(User)
                .where(User.email == email)
            )
            return result.scalar_one_or_none()
        
        except Exception as e:
            raise RepositoryError(f"Error retrieving user by email: {str(e)}") from e

    # endregion READ

    # region UPDATE

    async def update(self, db: AsyncSession, user_id: UUID, update_data: UserUpdateInDB) -> User:
        
        try:
            
            user = await self.get_by_id(db, user_id)

            if hasattr(update_data, "model_dump"):
                data = update_data.model_dump(exclude_unset=True, exclude_none=True)
            else:
                data = dict(update_data or {})

            for key, value in data.items():
                setattr(user, key, value)

            await db.flush()
            await db.refresh(user)
            return user
            
        except Exception as e:
            raise RepositoryError(f"Error updating user: {str(e)}") from e

    async def update_last_login(self, db: AsyncSession, user_id: UUID) -> User:
        
        try:
            
            user = await self.get_by_id(db, user_id)

            user.last_login = datetime.now(timezone.utc)
            
            await db.flush()
            await db.refresh(user)
            return user
        
        except Exception as e:
            raise RepositoryError(f"Error updating last_login: {str(e)}") from e
        
    async def add_role(self, db: AsyncSession, user_id: UUID, role_id: UUID) -> User:

        try:
            
            await db.execute(user_roles.insert().values(user_id = user_id, role_id = role_id))
            await db.flush()

            user = await self.get_by_id(db, user_id)

            await db.refresh(user)
            return user
        
        except Exception as e:
            raise RepositoryError(f"Error adding role to user: {str(e)}") from e
        
    async def remove_role(self, db: AsyncSession, user_id: UUID, role_id: UUID) -> User:
        
        try:
           
            user = await self.get_by_id(db, user_id)

            # Delete association if exists
            await db.execute(
                delete(user_roles).where(
                    user_roles.c.user_id == user_id,
                    user_roles.c.role_id == role_id
                )
            )

            await db.flush()
            await db.refresh(user)
            return user
        
        except Exception as e:
            raise RepositoryError(f"Error removing role from user: {str(e)}") from e

    # endregion UPDATE

    # region CHECK

    async def has_role(self, db: AsyncSession, user_id: UUID, role_id: UUID) -> bool:

        try:
            result = await db.execute(
                select(user_roles).where(
                    user_roles.c.user_id == user_id,
                    user_roles.c.role_id == role_id
                )
            )
            
            return result.first() is not None
        
        except Exception as e:
            raise RepositoryError(f"Error checking user role existence: {str(e)}") from e

    # endregion CHECK

    # region DELETE

    async def delete(self, db: AsyncSession, user_id: UUID) -> None:
        
        try:
            result = await db.execute( delete(User).where(User.id == user_id))

        except Exception as e:
            raise RepositoryError(f"Error deleting user: {str(e)}") from e

    # endregion DELETE



