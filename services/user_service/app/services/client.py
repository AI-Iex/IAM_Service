from typing import Optional, List
from uuid import UUID
import uuid
import logging
from app.services.interfaces.client import IClientService
from app.schemas.client import ClientCreate, ClientRead, ClientUpdate, ClientUpdateInDB, ClientPermissionAssign, ClientCreateResponse, ClientCreateInDB
from app.db.unit_of_work import UnitOfWorkFactory
from app.core.exceptions import DomainError, NotFoundError, EntityAlreadyExists
import secrets
from app.core.security import hash_password, verify_password
from app.repositories.interfaces.client import IClientRepository
from app.repositories.interfaces.permission import IPermissionRepository

logger = logging.getLogger(__name__)

class ClientService(IClientService):

    def __init__(self, 
                 client_repo: IClientRepository, 
                 permission_repo: IPermissionRepository, 
                 uow_factory: UnitOfWorkFactory):
        
        self._client_repo = client_repo
        self._permission_repo = permission_repo
        self._uow_factory = uow_factory

    # region CREATE

    async def create(self, payload: ClientCreate) -> ClientCreateResponse:

        """Create a new client."""

        # 0. Log the attempt
        logger.info("Trying to create a new client", extra = {"client_name": payload.name})

        async with self._uow_factory() as db:

            # 1. Check if the name is not already taken by another client
            client_with_name = await self._client_repo.read_with_filters( db = db, name = [payload.name], limit=1)
            if client_with_name:
                raise EntityAlreadyExists("Another client with the same name already exists")
            
            # 2. Generate client_id and secret
            client_id = uuid.uuid4()
            secret = secrets.token_hex(32)

            # 3. Hash the secret
            hashed_secret = hash_password(secret)

            client = ClientCreateInDB(
                name = payload.name,
                secret_hashed = hashed_secret,
                client_id = client_id,
                is_active = payload.is_active
            )

            # 4. Create client
            client_created = await self._client_repo.create(db = db, client = client)

            # 5. Log the success
            logger.info("Client created successfully", extra = {"client_id": client_created.id})

            # Return with plain secret
            return ClientCreateResponse(
                id = client_created.id,
                client_id = client_created.client_id,
                name = client_created.name,
                is_active = client_created.is_active,
                created_at = client_created.created_at,
                permissions = [],  # New client has no permissions yet
                secret = secret
            )

    # endregion CREATE

    # region READ

    async def read_by_id(self, client_id: UUID) -> ClientRead:

        """Get a client by its ID."""

        # 0. Log the attempt
        logger.info("Reading client by ID", extra = {"client_id": client_id})

        async with self._uow_factory() as db:

            # 1. Query the client
            client = await self._client_repo.read_by_id(db, client_id)

            # 2. Check if the client exists
            if not client:
                raise NotFoundError("Client not found")

            # 3. Log the success
            logger.info("Client retrieved successfully", extra = {"client_id": client.id})

            return ClientRead.model_validate(client)

    async def read_with_filters(self, name: Optional[str] = None, is_active: Optional[bool] = None, skip: int = 0, limit: int = 100) -> List[ClientRead]:

        """Get clients with filters."""

        # 0. Log the attempt
        logger.info(
            "Reading clients by filters", 
            extra={
                "name_filter": name, 
                "is_active_filter": is_active, 
                "skip": skip, 
                "limit": limit
            }
        )

        async with self._uow_factory() as db:

            #1 . Retrieve clients
            clients = await self._client_repo.read_with_filters(db, name, is_active, skip, limit)

            # 2. Log the success
            logger.info("Clients retrieved successfully", extra = {"retrieved_count": len(clients)})

            return [ClientRead.model_validate(client) for client in clients]

    # endregion READ

    # region UPDATE

    async def update(self, client_id: UUID, payload: ClientUpdate) -> ClientRead:

        """Update a client by its ID."""

        # 0. Log the attempt
        logger.info("Updating client by ID", extra={"client_id": client_id})

        async with self._uow_factory() as db:
            
            # 1. Retrieve the client and check existence
            existing = await self._client_repo.read_by_id(db, client_id)
            if not existing:
                raise NotFoundError("Client not found")
            
            # 2. Check if the new name (if provided) is not already taken by another client
            if payload.name and payload.name != existing.name:
                client_with_name = await self._client_repo.read_with_filters( db = db, name = [payload.name], limit=1)
                if client_with_name:
                    raise EntityAlreadyExists("Another client with the same name already exists")
                
            # 3. Prepare update data dict from ClientUpdate and separate permissions
            update_data = payload.model_dump(exclude_unset=True, exclude={'id'})  # exclude id and parameters that are not set
            permission_ids: list[UUID] | None = None  # initialize permission_ids
            perms_names = update_data.pop('permissions', None)  # separate permissions names to update it separately


            # 4. If permissions are provided, validate they exist and collect their ids
            if perms_names is not None:
                if len(perms_names) == 0:
                    permission_ids = []  # explicit request to clear permissions
                else:
                    # perms_names is expected to be a list of PermissionRef-like dicts
                    requested_names: list[str] = []
                    seen = set()
                    for ref in perms_names:
                        if isinstance(ref, dict):
                            name = ref.get("name")
                        else:
                            # if it's a pydantic model
                            name = getattr(ref, "name", None)

                        if not name:
                            raise DomainError("Permission references must include 'name'")

                        if name not in seen:
                            seen.add(name)
                            requested_names.append(name)

                    # fetch
                    permissions_found = await self._permission_repo.read_by_names(db, requested_names)

                    perm_map = {perm.name: perm for perm in permissions_found}
                    missing_perms = [n for n in requested_names if n not in perm_map]
                    if missing_perms:
                        raise NotFoundError(f"The following permissions do not exist: {missing_perms}")

                    permission_ids = [perm_map[n].id for n in requested_names]

            # 5. Create an internal DTO and update the client simple fields
            update_payload = ClientUpdateInDB(**update_data) if update_data else ClientUpdateInDB()
            updated_client = await self._client_repo.update(db, client_id, update_payload)

            # 6. If permissions were provided, perform assignment through repository method using ids
            if permission_ids is not None:
                updated_client = await self._client_repo.set_permissions(db, client_id, permission_ids)

            # 7. Log the success
            logger.info("Client updated successfully", extra={ "updated_client_id": updated_client.id})

            return ClientRead.model_validate(updated_client)
        
    async def add_permission(self, client_id: UUID, permission_id: UUID) -> ClientRead:
        
        """ Add permission to a client. """

        # 0. Log the attempt
        logger.info(
            "Adding permission to client",
            extra={
                "client_id": client_id,
                "permission_id": permission_id
            }
        )

        async with self._uow_factory() as db:

            # 1. Verify client exists
            client = await self._client_repo.read_by_id(db, client_id)
            if not client:
                raise NotFoundError("Client not found")

            # 2. Verify permission exists
            permission = await self._permission_repo.read_by_id(db, permission_id)
            if not permission:
                raise NotFoundError("Permission not found")

            # 3. If already assigned, raise error
            exists = await self._client_repo.has_permission(db, client_id, permission_id)
            if exists:
                raise EntityAlreadyExists("Client already has this permission")

            # 4. Assign the permission
            updated = await self._client_repo.add_permission(db, client_id, permission_id)

            # 5. Log the success
            logger.info(
                "Permission added to client successfully",
                extra={
                    "client_id": client_id,
                    "permission_id": permission_id
                }
            )

            return ClientRead.model_validate(updated)

    async def remove_permission(self, client_id: UUID, permission_id: UUID) -> ClientRead:
        
        """Remove a permission from a client."""

        # 0. Log the attempt
        logger.info(
            "Removing permission from client",
            extra={
                "client_id": client_id,
                "permission_id": permission_id
            }
        )

        async with self._uow_factory() as db:
            
            # 1. Verify client exists
            client = await self._client_repo.read_by_id(db, client_id)
            if not client:
                raise NotFoundError("Client not found")

            # 2. Verify permission exists
            permission = await self._permission_repo.read_by_id(db, permission_id)
            if not permission:
                raise NotFoundError("Permission not found")
            
            # 3. If not assigned, raise error
            exists = await self._client_repo.has_permission(db, client_id, permission_id)
            if not exists:
                raise EntityAlreadyExists("Client does not have this permission")

            # 4. Remove the permission
            updated = await self._client_repo.remove_permission(db, client_id, permission_id)

            # 5. Log the success
            logger.info(
                "Permission removed from client",
                extra={
                    "client_id": client_id,
                    "permission_id": permission_id
                }
            )

            return ClientRead.model_validate(updated)

    # endregion UPDATE

    # region DELETE

    async def delete(self, client_id: UUID) -> None:
        
        """Delete a client by its ID."""

        # 0. Log the attempt
        logger.info("Deleting client by ID", extra={"client_id": client_id})

        async with self._uow_factory() as db:

            # 1. Retrieve the client
            existing_client = await self._client_repo.read_by_id(db, client_id)

            # 2. Check if the client exists
            if not existing_client:
                raise NotFoundError("Client not found")

            # 3. Delete the client
            await self._client_repo.delete(db, client_id)

            # 4. Log the success
            logger.info("Client deleted successfully", extra={"deleted_client_id": client_id})

    # endregion DELETE