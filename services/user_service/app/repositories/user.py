from typing import Optional, List
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from app.models.user import User
from app.schemas.user import UserCreateInDB
from app.core.exceptions import EntityAlreadyExists, RepositoryError
from app.repositories.interfaces import IUserRepository
from uuid import UUID

class UserRepository(IUserRepository):

    # region CREATE

    async def create(self, db: AsyncSession, dto: UserCreateInDB) -> User:
        try:
            user = User(
                email=dto.email,
                full_name=dto.full_name,
                hashed_password=dto.hashed_password,
                is_active=dto.is_active,
                is_superuser=dto.is_superuser
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

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        result = await db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, db: AsyncSession, user_id: UUID) -> Optional[User]:   
        result = await db.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.roles))
        )
        return result.scalar_one_or_none() 

    async def get_by_name(self, db: AsyncSession, name: str, skip: int = 0, limit: int = 100) -> List[User]:
        result = await db.execute(
            select(User)
            .where(User.full_name.ilike(f"%{name}%"))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    # endregion READ

    # region UPDATE

    async def update(self, db: AsyncSession, user_id: UUID, update_data: dict) -> Optional[User]:
        try:
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            if user:
                for key, value in update_data.items():
                    setattr(user, key, value)
                await db.refresh(user)
            return user
        except Exception as e:
            raise RepositoryError(f"Error updating user: {str(e)}") from e

    # endregion UPDATE

    # region DELETE

    async def delete(self, db: AsyncSession, user_id: UUID) -> bool:
        try:
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            if user:
                await db.delete(user)
                return True
            return False
        except Exception as e:
            raise RepositoryError(f"Error deleting user: {str(e)}") from e

    # endregion DELETE

    # region LIST

    async def get_all(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
        result = await db.execute(
            select(User)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_active(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
        result = await db.execute(
            select(User)
            .where(User.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_superusers(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
        result = await db.execute(
            select(User)
            .where(User.is_superuser == True)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    # endregion LIST