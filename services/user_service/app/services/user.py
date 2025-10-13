from app.repositories.interfaces import IUserRepository
from app.db.unit_of_work import UnitOfWorkFactory
from app.schemas.user import UserCreate, UserCreateInDB, UserRead
from app.db.unit_of_work import unit_of_work
from app.core.security import hash_password
from app.core.exceptions import EntityAlreadyExists, DomainError
import logging

logger = logging.getLogger("nebulaops.user_service")

class UserService:
    def __init__(self, user_repo: IUserRepository, uow_factory: UnitOfWorkFactory = unit_of_work):
        self.user_repo = user_repo
        self.uow_factory = uow_factory

# region CREATE

    # Create a new user
    def create(self, payload: UserCreate) -> UserRead :
        
        # 0. Log the attempt
        logger.info("Creating user", extra={"email": payload.email})

        # 1. Validate email format
        if not payload.email or "@" not in payload.email:
            raise DomainError("Invalid email format")
        
        with self.uow_factory() as db:

            # 2. Check if email already exists
            existing = self.user_repo.get_by_email(db, payload.email)
            if existing:
                raise EntityAlreadyExists("Email is already in use")

            # 3. Hash the password and prepare DTO for repository
            hashed = hash_password(payload.password)
            dto = UserCreateInDB(
                email=payload.email,
                full_name=payload.full_name,
                hashed_password=hashed,
                is_active=payload.is_active,
                is_superuser=payload.is_superuser
            )

            # 4. Create the user in the database
            user = self.user_repo.create(db, dto)
            
            # 5. Build a plain dict while session is still open to avoid DetachedInstanceError
            user_schema = UserRead.model_validate(user)

            # 6. Log the success
            logger.info("User created successfully", extra={"user_id": user.id, "email": payload.email})
            
        return user_schema
    
# endregion CREATE
