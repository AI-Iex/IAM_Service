from datetime import datetime, timedelta, timezone
from typing import Optional, List
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, delete, update
from app.models.user import User
from app.schemas.user import UserCreateInDB
from app.core.exceptions import EntityAlreadyExists, RepositoryError
from app.repositories.interfaces.user import IUserRepository
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

    async def get_with_filters(
        self,
        db: AsyncSession,
        name: Optional[str] = None,
        email: Optional[str] = None,
        active: Optional[bool] = None,
        is_superuser: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
    
        query = select(User).options(selectinload(User.roles))
        
        if name is not None:
            query = query.where(User.full_name.ilike(f"%{name}%"))
        
        if email is not None:
            query = query.where(User.email == email)
        
        if active is not None:
            query = query.where(User.is_active == active)
        
        if is_superuser is not None:
            query = query.where(User.is_superuser == is_superuser)
        
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()


    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        result = await db.execute(
            select(User)
            .where(User.email == email)
            .options(selectinload(User.roles))
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, db: AsyncSession, user_id: UUID) -> Optional[User]:   
        result = await db.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.roles))
        )
        return result.scalar_one_or_none() 

    # endregion READ

    # region UPDATE

    async def update(self, db: AsyncSession, user_id: UUID, update_data: dict) -> User:
        try:
            result = await db.execute(
                select(User)
                .where(User.id == user_id)
                .options(selectinload(User.roles))
            )
            user = result.scalar_one_or_none()
            if user:
                for key, value in update_data.items():
                    setattr(user, key, value)
                
                await db.flush()
                await db.refresh(user)
                return user
        except Exception as e:
            raise RepositoryError(f"Error updating user: {str(e)}") from e
        

    async def update_last_login(self, db: AsyncSession, user_id: UUID) -> User:
        try:
            result = await db.execute(
                select(User)
                .where(User.id == user_id)
                .options(selectinload(User.roles))
            )
            user = result.scalar_one_or_none()
            if user:
                user.last_login = datetime.now(timezone.utc)
                
                await db.flush()
                await db.refresh(user)
                return user
        except Exception as e:
            raise RepositoryError(f"Error updating last_login: {str(e)}") from e
    # endregion UPDATE

    # region DELETE

    async def delete(self, db: AsyncSession, user_id: UUID) -> None:
        try:
            
            result = await db.execute( delete(User).where(User.id == user_id))

        except Exception as e:
            raise RepositoryError(f"Error deleting user: {str(e)}") from e

    # endregion DELETE
