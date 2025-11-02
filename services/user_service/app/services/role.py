from typing import Optional, List
from uuid import UUID
from app.db.unit_of_work import UnitOfWorkFactory, async_unit_of_work
from app.repositories.interfaces.role import IRoleRepository
from app.schemas.role import RoleCreate, RoleRead, RoleUpdate, RoleUpdateInDB
from app.services.interfaces.role import IRoleService
import logging
from app.core.exceptions import EntityAlreadyExists, DomainError, NotFoundError
from app.repositories.interfaces.permission import IPermissionRepository


logger = logging.getLogger(__name__)

class RoleService(IRoleService):

    def __init__(self, role_repo: IRoleRepository, permission_repo: IPermissionRepository, uow_factory: UnitOfWorkFactory = async_unit_of_work): 
        self._role_repo = role_repo
        self._permission_repo = permission_repo
        self._uow_factory = uow_factory

# region CREATE

    # Create a new role
    async def create(self, payload: RoleCreate) -> RoleRead:

        """Create a new role."""

        # 0. Log the attempt
        logger.info("Trying to create a new role", extra = {"extra": {"name": payload.name}})
        
        async with self._uow_factory() as db:
            
            # 1. Check if the name is not null or empty
            if not payload.name or not payload.name.strip():
                raise DomainError("Role name cannot be empty")
            
            # 2. Check if the role already exists
            existing_roles = await self._role_repo.read_with_filters( db = db, name = [payload.name], limit=1)
            if existing_roles:
                raise EntityAlreadyExists("Role with the same name already exists")
            
            # 3. Create the role
            role = await self._role_repo.create(db = db, role = payload)

            # 4. Log the success
            logger.info("Role created successfully", extra = {"extra": {"role_id": role.id}})

            return RoleRead.model_validate(role)

#endregion CREATE

#region READ

    # Get a role by its ID
    async def read_by_id(self, role_id: UUID) -> RoleRead:

        """Get a role by its ID."""
       
        # 0. Log the attempt
        logger.info("Reading role by ID", extra = {"extra": { "retrieve_role_id": role_id}})

        async with self._uow_factory() as db:
            
            # 1. Retrieve the role
            role = await self._role_repo.read_by_id(db, role_id)

            # 2. Check if the role exists
            if not role:
                raise NotFoundError("Role not found")

            # 3. Log the success
            logger.info("Role read successfully", extra = {"extra": { "role_found": role.id}})

            return RoleRead.model_validate(role)

    # Get roles with filters
    async def read_with_filters(
        self, 
        name: Optional[List[str]] = None, 
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
            logger.info("Roles retrieved successfully", extra={"Roles read count": len(roles)})

            return [RoleRead.model_validate(role) for role in roles]

#endregion READ

#region UPDATE

    # Update a role by its ID
    async def update(self, role_id: UUID, role: RoleUpdate) -> RoleRead:

        """Update a role by its ID."""

        # 0. Log the attempt
        logger.info("Updating role by ID", extra = {"role_id": role_id})

        async with self._uow_factory() as db:

            # 1. Retrieve the role and check existence
            existing_role = await self._role_repo.read_by_id(db, role_id)
            if not existing_role:
                raise NotFoundError("Role not found")
            
            # 2 Check if the new name (if provided) is not already taken by another role
            if role.name and role.name != existing_role.name:
                role_with_name = await self._role_repo.read_with_filters( db = db, name = [role.name], limit=1)
                if role_with_name:
                    raise EntityAlreadyExists("Another role with the same name already exists")
                
            # 3. Prepare update data dict from RoleUpdate and separate permissions
            update_data = role.model_dump(exclude_unset = True, exclude = {'id'}) # exclude id and parameters that are not set
            permission_ids: list[UUID] | None = None # initialize permission_ids
            perms_names = update_data.pop('permissions', None) # separate permissions names to update it separately

            # 4. If permissions are provided, validate they exist and collect their ids
            if perms_names is not None:
                if len(perms_names) == 0:
                    permission_ids = []  # explicit request to clear permissions
                else:
                    # get permissions by names from permission repository
                    permissions = await self._permission_repo.read_by_names(db, perms_names)
                    if len(permissions) != len(perms_names):
                        missing_perms = set(perms_names) - {perm.name for perm in permissions}
                        raise NotFoundError(f"The following permissions do not exist: {missing_perms}")
                    permission_ids = [p.id for p in permissions]

            # 5. Create an internal DTO and update the role simple fields
            update_payload = RoleUpdateInDB(**update_data) if update_data else RoleUpdateInDB()
            updated_role = await self._role_repo.update(db, role_id, update_payload)

            # 6. If permissions were provided, perform assignment through repository method using ids
            if permission_ids is not None:
                updated_role = await self._role_repo.set_permissions(db, role_id, permission_ids)

            # 7. Log the success
            logger.info("Role updated successfully", extra = {"extra": { "updated_role_id": updated_role.id}})

            return RoleRead.model_validate(updated_role)

    # Add a permission to a role
    async def add_permission(self, role_id: UUID, permission_id: UUID) -> RoleRead:

        """ Add a permission to a role. """

        # 0. Log the attempt
        logger.info(
            "Adding permission to role", 
            extra = {
                "extra": {
                    "role_id": role_id, 
                    "permission_id": permission_id}
            }
        )

        async with self._uow_factory() as db:

            # 1. Verify role exists
            role = await self._role_repo.read_by_id(db, role_id)
            if not role:
                raise NotFoundError("Role not found")

            # 2. Verify permission exists
            permission = await self._permission_repo.read_by_id(db, permission_id)
            if not permission:
                raise NotFoundError("Permission not found")
            
            # 3. If already assigned, raise error
            exists = await self._role_repo.has_permission(db, role_id, permission_id)
            if exists:
                raise EntityAlreadyExists("Role already has this permission")  

            # 4. Add the permission
            updated = await self._role_repo.add_permission(db, role_id, permission_id)

            # 5. Log the success
            logger.info(
                "Permission added to role successfully", 
                extra = {
                    "extra": {
                        "role_id": role_id, 
                        "permission_id": permission_id}
                }
            )

            return RoleRead.model_validate(updated)

    # Remove a permission from a role
    async def remove_permission(self, role_id: UUID, permission_id: UUID) -> RoleRead:

        """Remove a permission from a role."""

        # 0. Log the attempt
        logger.info(
            "Removing permission from role", 
            extra = {
                "extra": {
                    "role_id": role_id, 
                    "permission_id": permission_id}
            }
        )

        async with self._uow_factory() as db:
            
            # 1. Verify role exists
            role = await self._role_repo.read_by_id(db, role_id)
            if not role:
                raise NotFoundError("Role not found")

            # 2. Verify permission exists
            permission = await self._permission_repo.read_by_id(db, permission_id)
            if not permission:
                raise NotFoundError("Permission not found")
            
            # 3. If not assigned, raise error
            exists = await self._role_repo.has_permission(db, role_id, permission_id)
            if not exists:
                raise EntityAlreadyExists("Role does not have this permission")

            # 4. Remove the permission
            updated = await self._role_repo.remove_permission(db, role_id, permission_id)

            # 5. Log the success
            logger.info(
                "Permission removed from role", 
                extra = {
                    "extra": {
                        "role_id": role_id, 
                        "permission_id": permission_id}
                }
            )

            return RoleRead.model_validate(updated)

#endregion UPDATE

#region DELETE

    # Delete a role by its ID
    async def delete(self, role_id: UUID) -> None:

        """Delete a role by its ID."""

        # 0. Log the attempt
        logger.info("Deleting role by ID", extra = {"role_id": role_id})

        async with self._uow_factory() as db:

            # 1. Retrieve the role
            existing_role = await self._role_repo.read_by_id( db, role_id)

            # 2. Check if the role exists
            if not existing_role:
                raise NotFoundError("Role not found")

            # 3. Delete the role
            await self._role_repo.delete( db, role_id)

            # 4. Log the success
            logger.info("Role deleted successfully", extra = {"extra": { "deleted_role_id": role_id}})

#endregion DELETE
