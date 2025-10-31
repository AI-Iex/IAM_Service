from typing import Optional, List
from uuid import UUID
from app.db.unit_of_work import UnitOfWorkFactory, async_unit_of_work
from app.repositories.interfaces.role import IRoleRepository
from app.schemas.role import RoleCreate, RoleRead, RoleUpdate
from app.services.interfaces.role import IRoleService
import logging, re
from app.core.exceptions import EntityAlreadyExists, DomainError, NotFoundError

logger = logging.getLogger(__name__)

class RoleService(IRoleService):

    def __init__(self, role_repo: IRoleRepository, uow_factory: UnitOfWorkFactory = async_unit_of_work): 
        self._role_repo = role_repo
        self._uow_factory = uow_factory


    async def create(self, payload: RoleCreate) -> RoleRead:

        """Create a new role."""

        # 0. Log the attempt
        logger.info("Trying to create a new role", extra={"extra": {"name": payload.name}})
        
        async with self._uow_factory() as db:
            
            # 1. Check if the name is not null or empty
            if not payload.name or not payload.name.strip():
                raise DomainError("Role name cannot be empty")
            
            # 2. Check if the role already exists
            existing_roles = await self._role_repo.read_with_filters( db = db, name = payload.name, limit=1)
            if existing_roles:
                raise EntityAlreadyExists("Role with the same name already exists")
            
            # 3. Create the role
            role = await self._role_repo.create(db = db, role = payload)

            # 4. Log the success
            logger.info("Role created successfully", extra={"extra": {"role_id": str(role.id)}})

            return RoleRead.model_validate(role)


    async def read_by_id(self, role_id: UUID) -> RoleRead:

        """Get a role by its ID."""
       
        # 0. Log the attempt
        logger.info(
            "Reading role by ID",
            extra = {
                "extra": { "retrieve_role_id": role_id}
            }
        )

        async with self._uow_factory() as db:
            
            # 1. Retrieve the role
            role = await self._role_repo.read_by_id(db, role_id)

            # 2. Check if the role exists
            if not role:
                raise NotFoundError("Role not found")

            # 3. Log the success
            logger.info(
                "Role read successfully",
                extra = {
                    "extra": { "role_found": role.id}
                }
            )

            return RoleRead.model_validate(role)


    async def read_with_filters(
        self, 
        name: Optional[str] = None, 
        description: Optional[str] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[RoleRead]:
        
        """Get roles with filters."""

        # 0. Log the attempt
        logger.info(
            "Reading roles by filters",
            extra = {
                "name_filter": name, 
                "description_filter": description, 
                "skip": skip, 
                "limit": limit
            }
        )

        async with self._uow_factory() as db:

            # 1. Retrieve the roles
            roles = await self._role_repo.read_with_filters(
                db,
                name,
                description,
                skip,
                limit
            )

            # 2. Log the success
            logger.info(
                "Roles retrieved successfully", 
                extra={
                    "Roles read count": len(roles)
                }
            )

            return [RoleRead.model_validate(role) for role in roles]


    async def update(self, role_id: UUID, role: RoleUpdate) -> RoleRead:

        """Update a role by its ID."""

        # 0. Log the attempt
        logger.info(
            "Updating role by ID",
            extra = {
                "role_id": role_id
            }
        )

        async with self._uow_factory() as db:

            # 1. Retrieve the role
            existing_role = await self._role_repo.read_by_id(db, role_id)

            # 2. Check if the role exists
            if not existing_role:
                raise NotFoundError("Role not found")
            
            # 3 Check if the new name (if provided) is not already taken by another role
            if role.name and role.name != existing_role.name:
                role_with_name = await self._role_repo.read_with_filters( db = db, name = role.name, limit=1)
                if role_with_name:
                    raise EntityAlreadyExists("Another role with the same name already exists")

            # 4. Update the role
            updated_role = await self._role_repo.update( db, role_id, role)

            # 5. Log the success
            logger.info(
                "Role updated successfully",
                extra = {
                    "extra": { "updated_role_id": updated_role.id}
                }
            )

            return RoleRead.model_validate(updated_role)


    async def delete(self, role_id: UUID) -> None:

        """Delete a role by its ID."""

        # 0. Log the attempt
        logger.info(
            "Deleting role by ID",
            extra = {
                "role_id": role_id
            }
        )

        async with self._uow_factory() as db:

            # 1. Retrieve the role
            existing_role = await self._role_repo.read_by_id( db, role_id)

            # 2. Check if the role exists
            if not existing_role:
                raise NotFoundError("Role not found")

            # 3. Delete the role
            await self._role_repo.delete( db, role_id)

            # 4. Log the success
            logger.info(
                "Role deleted successfully",
                extra = {
                    "extra": { "deleted_role_id": role_id}
                }
            )
