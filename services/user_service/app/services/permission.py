from typing import Optional, List
from uuid import UUID
import logging
from app.services.interfaces.permission import IPermissionService
from app.repositories.interfaces.permission import IPermissionRepository
from app.schemas.permission import PermissionCreate, PermissionRead, PermissionUpdate
from app.db.unit_of_work import UnitOfWorkFactory, async_unit_of_work
from app.core.exceptions import DomainError, NotFoundError, EntityAlreadyExists

logger = logging.getLogger(__name__)


class PermissionService(IPermissionService):

    def __init__(self, permission_repo: IPermissionRepository, uow_factory: UnitOfWorkFactory = async_unit_of_work):
        self._permission_repo = permission_repo
        self._uow_factory = uow_factory


    async def create(self, payload: PermissionCreate) -> PermissionRead:
                
        """Create a new permission."""

        # 0. Log the attempt
        logger.info("Trying to create a new permission", extra={"extra": {"name": payload.name}})
        
        async with self._uow_factory() as db:
            
            # 1. Check if the name is not null or empty
            if not payload.name or not payload.name.strip():
                raise DomainError("Permission name cannot be empty")
            
            # 2. Check if the permission already exists
            existing_permissions = await self._permission_repo.read_with_filters( db = db, name = payload.name, limit=1)
            if existing_permissions:
                raise EntityAlreadyExists("Permission with the same name already exists")
            
            # 3. Create the permission
            permission = await self._permission_repo.create(db = db, payload = payload)

            # 4. Log the success
            logger.info("Permission created successfully", extra={"extra": {"permission_id": str(permission.id)}})

            return PermissionRead.model_validate(permission)


    async def read_by_id(self, permission_id: UUID) -> PermissionRead:
        
        """Get a permission by its ID."""
       
        # 0. Log the attempt
        logger.info(
            "Reading permission by ID",
            extra = {
                "extra": { "retrieve_permission_id": permission_id}
            }
        )

        async with self._uow_factory() as db:
            
            # 1. Retrieve the permission
            permission = await self._permission_repo.read_by_id(db, permission_id)

            # 2. Check if the permission exists
            if not permission:
                raise NotFoundError("Permission not found")

            # 3. Log the success
            logger.info(
                "Permission read successfully",
                extra = {
                    "extra": { "permission_found": permission.id}
                }
            )

            return PermissionRead.model_validate(permission)


    async def read_with_filters(self, 
                                name: Optional[str] = None, 
                                description: Optional[str] = None, 
                                skip: int = 0, 
                                limit: int = 100
                                ) -> List[PermissionRead]:
        
        """Get permissions with filters."""

        # 0. Log the attempt
        logger.info(
            "Reading permissions by filters",
            extra = {
                "name_filter": name, 
                "description_filter": description, 
                "skip": skip, 
                "limit": limit
            }
        )

        async with self._uow_factory() as db:

            # 1. Retrieve the permissions
            permissions = await self._permission_repo.read_with_filters(
                db,
                name,
                description,
                skip,
                limit
            )

            # 2. Log the success
            logger.info(
                "Permissions retrieved successfully",
                extra={
                    "Permissions read count": len(permissions)
                }
            )

            return [PermissionRead.model_validate(permission) for permission in permissions]


    async def update(self, permission_id: UUID, payload: PermissionUpdate) -> PermissionRead:
        
        """Update a permission by its ID."""

        # 0. Log the attempt
        logger.info(
            "Updating permission by ID",
            extra = {
                "permission_id": permission_id
            }
        )

        async with self._uow_factory() as db:

            # 1. Retrieve the permission
            existing_permission = await self._permission_repo.read_by_id(db, permission_id)

            # 2. Check if the permission exists
            if not existing_permission:
                raise NotFoundError("Permission not found")

            # 3 Check if the new name (if provided) is not already taken by another permission
            if payload.name and payload.name != existing_permission.name:
                permission_with_name = await self._permission_repo.read_with_filters( db = db, name = payload.name, limit=1)
                if permission_with_name:
                    raise EntityAlreadyExists("Another permission with the same name already exists")

            # 4. Update the permission
            updated_permission = await self._permission_repo.update( db, permission_id, payload)

            # 5. Log the success
            logger.info(
                "Permission updated successfully",
                extra = {
                    "extra": { "updated_permission_id": updated_permission.id}
                }
            )

            return PermissionRead.model_validate(updated_permission)


    async def delete(self, permission_id: UUID) -> None:
        
        """Delete a permission by its ID."""

        # 0. Log the attempt
        logger.info(
            "Deleting permission by ID",
            extra = {
                "permission_id": permission_id
            }
        )

        async with self._uow_factory() as db:

            # 1. Retrieve the permission
            existing_permission = await self._permission_repo.read_by_id( db, permission_id)

            # 2. Check if the permission exists
            if not existing_permission:
                raise NotFoundError("Permission not found")

            # 3. Delete the permission
            await self._permission_repo.delete( db, permission_id)

            # 4. Log the success
            logger.info(
                "Permission deleted successfully",
                extra = {
                    "extra": { "deleted_permission_id": permission_id}
                }
            )
