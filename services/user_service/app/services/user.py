from typing import List, Optional
from app.repositories.interfaces import IUserRepository
from app.services.interfaces import IUserService
from app.db.unit_of_work import UnitOfWorkFactory
from app.schemas.user import UserCreate, UserCreateInDB, UserRead, UserUpdate
from app.db.unit_of_work import async_unit_of_work
from app.core.security import hash_password
from app.core.exceptions import EntityAlreadyExists, DomainError, NotFoundError
import logging, re
from app.core.business_config import BusinessConfig
from uuid import UUID

logger = logging.getLogger("nebulaops.user_service")

class UserService(IUserService):
    def __init__(self, user_repo: IUserRepository, uow_factory: UnitOfWorkFactory = async_unit_of_work): 
        self.user_repo = user_repo
        self.uow_factory = uow_factory
        self.policy = BusinessConfig.load()

# region Internal Methods (Validation)

    # Method to validate password business rules
    def _validate_password(self, password: str):

        # Load password policy from business config
        password_rules = self.policy["password_policy"]

        # Check length
        if len(password) < password_rules["min_length"]:
            raise DomainError(f"Password must be at least {password_rules['min_length']} characters long")
        
        # Get character requirements
        char_rules = password_rules["character_requirements"]

        # Check uppercase
        if char_rules["uppercase"]["required"]:
            if sum(1 for c in password if c.isupper()) < char_rules["uppercase"]["min_count"]:
                raise DomainError("Password must contain at least one uppercase letter")
            
        # Check numbers
        if char_rules["numbers"]["required"]:
            if sum(1 for c in password if c.isdigit()) < char_rules["numbers"]["min_count"]:
                raise DomainError("Password must contain at least one number")

        # Check special characters
        if char_rules["special_chars"]["required"]:
            allowed = char_rules["special_chars"]["allowed_chars"]
            pattern = f"[{re.escape(allowed)}]"
            if len(re.findall(pattern, password)) < char_rules["special_chars"]["min_count"]:
                raise DomainError(
                    f"Password must contain at least one special character ({allowed})"
                )

    # Method to validate name business rules
    def _validate_name(self, name: str):

        # Load name policy from business config
        name_rules = self.policy["name_policy"]

        # Check length
        if len(name.strip()) < name_rules["min_length"]:
            raise DomainError(f"Name must be at least {name_rules['min_length']} characters long")

        # Get character requirements / restrictions
        char_rules = name_rules.get("character_requirements", {})

        # Numbers rule: if numbers are not allowed, fail on any digit
        numbers_rule = char_rules.get("numbers", {"allowed": True})
        numbers_allowed = numbers_rule.get("allowed", True)
        if not numbers_allowed:
            for char in name:
                if char in "0123456789": 
                    raise DomainError("Name cannot contain numbers")

        # Special characters rule: if special chars are not allowed, only the listed allowed_special_chars are permitted
        special_rule = char_rules.get("special_chars", {"allowed": True, "allowed_special_chars": ""})
        special_allowed = special_rule.get("allowed", True)
        allowed_special = special_rule.get("allowed_special_chars", "")

        if not special_allowed:
            for c in name:
                # Letters are always allowed
                if c.isalpha():
                    continue
                # Numbers allowed depending on numbers_rule
                if numbers_allowed and c in "0123456789":
                    continue
                # Allowed special characters (including space) are permitted
                if c in allowed_special:
                    continue
                # If we reach here, the character is invalid
                raise DomainError(f"Name has this character '{c}' not allowed. Special chars allowed: '{allowed_special}'")

        # Passed all checks
        return True
    
    # Method to validate email business rules
    def _validate_email(self, email: str) -> bool:

        # Load email policy from business config
        email_policy = self.policy.get("email_policy", {})
        
        # Clean and normalize email
        email = email.strip().lower()
        
        # 1. Validate length
        min_length = email_policy.get("min_length", 0)
        max_length = email_policy.get("max_length", 255)
        
        if len(email) < min_length:
            raise DomainError(f"Email must be at least {min_length} characters long")
        
        if len(email) > max_length:
            raise DomainError(f"Email cannot exceed {max_length} characters")
        
        # 2. Validate basic format
        if not self._is_valid_email_format(email):
            raise DomainError("Invalid email format")
        
        # 3. Extract domain for validation
        try:
            domain = email.split('@')[1]
        except IndexError:
            raise DomainError("Invalid email format - missing domain")
        
        # 4. Validate domain against allowed domains
        valid_domains = email_policy.get("valid_domains", [])
        if valid_domains and domain not in valid_domains:
            allowed_domains = ", ".join(valid_domains)
            raise DomainError(f"Email domain not allowed. Valid domains: {allowed_domains}")
        
        # 5. Additional security checks
        self._validate_email_security(email)
        
        return True

    # Basic RFC-compliant email format validation
    def _is_valid_email_format(self, email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    # Additional security validations for email
    def _validate_email_security(self, email: str):
        
        # Check for consecutive dots
        if '..' in email:
            raise DomainError("Invalid email format - consecutive dots are not allowed")
        
        # Check for dot at the beginning or end of local part
        local_part = email.split('@')[0]
        if local_part.startswith('.') or local_part.endswith('.'):
            raise DomainError("Invalid email format - local part cannot start or end with a dot")

# endregion Internal Methods

# region CREATE

    # Create a new user
    async def create(self, payload: UserCreate) -> UserRead :
        
        # 0. Log the attempt
        logger.info("Creating user", extra={"email": payload.email})

        # 1. Validate email format
        self._validate_email(payload.email)
        
        # 2. Validate password policy
        self._validate_password(payload.password)

        # 3. Validate name policy
        self._validate_name(payload.full_name)

        async with self.uow_factory() as db:

            # 4. Check if email already exists
            existing = await self.user_repo.get_by_email(db, payload.email)
            if existing:
                raise EntityAlreadyExists("Email is already in use")

            # 5. Hash the password and prepare DTO for repository
            hashed = hash_password(payload.password)
            dto = UserCreateInDB(
                email=payload.email,
                full_name=payload.full_name,
                hashed_password=hashed,
                is_active=payload.is_active,
                is_superuser=payload.is_superuser
            )

            # 6. Create the user in the database
            user = await self.user_repo.create(db, dto)

            # 7. Build a plain dict while session is still open to avoid DetachedInstanceError
            user_schema = UserRead.model_validate(user)

            # 8. Log the success
            logger.info("User created successfully", extra = {"user_id": user.id, "email": payload.email})
            
        return user_schema
    
# endregion CREATE

# region READ

    # Read a user by ID
    async def read_by_id(self, user_id: UUID) -> Optional[UserRead]:
        
        # 0. Log the attempt
        logger.info("Reading user", extra={"user_id": user_id})

        async with self.uow_factory() as db:

            # 1. Query the user
            user = await self.user_repo.get_by_id(db, user_id)

            # 2. Check if user exists
            if not user:
                raise NotFoundError("User not found")
            
            # 3. Build a plain dict while session is still open to avoid DetachedInstanceError
            user_schema = UserRead.model_validate(user)

            # 4. Log the success
            logger.info("User read successfully", extra = {"user_id": user_id})

        return user_schema

    # Read a user by email
    async def read_by_email(self, email: str) -> UserRead:
        
        # 0. Log the attempt
        logger.info("Reading user", extra={"email": email})

        # 1. Check if email is valid
        if not email or "@" not in email:
            raise DomainError("Invalid email format")

        async with self.uow_factory() as db:

            # 2. Query the user
            user = await self.user_repo.get_by_email(db, email)

            # 3. Check if user exists
            if not user:
                raise NotFoundError("User not found")

            # 4. Build a plain dict while session is still open to avoid DetachedInstanceError
            user_schema = UserRead.model_validate(user)

            # 5. Log the success
            logger.info("User read successfully", extra = {"email": email})

        return user_schema
    
    # Read users by name
    async def read_by_name(self, name: str, skip: int = 0, limit: int = 100) -> list[UserRead]:
        
        # 0. Log the attempt
        logger.info("Reading users by name", extra={"query_name": name, "skip": skip, "limit": limit})

        # 1. Validate name
        if not name or len(name.strip()) < 2:
            raise DomainError("Invalid name format")

        async with self.uow_factory() as db:

            # 2. Query users by name with pagination
            users = await self.user_repo.get_by_name(db, name = name, skip = skip, limit = limit)

            # 3. If no users found, return empty list (expected for searches)
            if not users:
                logger.info("No users found for name", extra = {"query_name": name})
                return []

            # 4. Build Pydantic schemas while session is open to avoid DetachedInstanceError
            user_schemas = [UserRead.model_validate(user) for user in users]

            # 5. Log the success
            logger.info("Users read successfully", extra = {"query_name": name, "count": len(user_schemas)})

        return user_schemas
    
# endregion READ

    async def delete(self, user_id: UUID) -> bool:
        raise NotImplementedError("Delete method not implemented")

    async def read_all(self, skip: int, limit: int) -> List[UserRead]:
        return []

    async def read_active(self, skip: int, limit: int) -> List[UserRead]:
        return []

    async def read_superusers(self, skip: int, limit: int) -> List[UserRead]:
        return []

    async def update(self, user_id: UUID, payload) -> Optional[UserRead]:
        raise NotImplementedError("Update method not implemented")
