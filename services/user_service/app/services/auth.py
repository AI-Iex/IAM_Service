from app.services.interfaces.auth import IAuthService
from app.db.unit_of_work import UnitOfWorkFactory
from app.core.exceptions import DomainError, NotFoundError
from app.schemas.user import UserRead
from app.core.security import (
    verify_password, create_user_access_token, create_client_access_token,
    generate_raw_refresh_token, hash_refresh_token,
    refresh_token_expiry_datetime
)
import hmac, logging, datetime
from uuid import UUID
from app.repositories.interfaces.user import IUserRepository
from app.repositories.interfaces.refresh_token import IRefreshTokenRepository
from app.repositories.interfaces.client import IClientRepository
from app.repositories.client import ClientRepository
from app.schemas.auth import TokenPair, UserAndToken

logger = logging.getLogger(__name__)


class AuthService(IAuthService):


    def __init__(self,  
                 uow_factory: UnitOfWorkFactory, 
                 user_repo: IUserRepository, 
                 refresh_token_repo: IRefreshTokenRepository, 
                 client_repo: IClientRepository):
        
        self.uow_factory = uow_factory
        self.user_repo = user_repo
        self.refresh_repo = refresh_token_repo
        self.client_repo = client_repo


    async def login(self, email: str, password: str, ip: str = None, user_agent: str = None) -> UserAndToken:
        
        ''' Authenticate a user and return user + tokens '''

        # 0. Log the attempt
        logger.info(
            "Login user",
            extra={
                "email": email,
                "ip": ip
            }
        )

        async with self.uow_factory() as db:

            # 1. Get user by email
            user = await self.user_repo.get_by_email(db, email)
            if not user:
                raise NotFoundError("Invalid credentials")

            # 2. Verify password
            if not verify_password(password, user.hashed_password):
                raise DomainError("Invalid credentials")

            # 3. Update last_login
            await self.user_repo.update_last_login(db, user.id)

            # 4. Create access token
            role_names = [r.name for r in user.roles] if getattr(user, 'roles', None) else []
            access_token_pair = create_user_access_token(subject = str(user.id), roles = role_names, is_superuser = user.is_superuser)
            access_token = access_token_pair.access_token
            expires_in = access_token_pair.expires_in

            # 4.1 Log the created access token
            logger.info("Access token created", extra={"request_by_user_id": user.id})

            # 5. Generate refresh token (raw + jti) and save hash in DB
            raw_refresh_token, jti_refresh_token = generate_raw_refresh_token()

            # 6. Hash the raw refresh token
            hashed = hash_refresh_token(raw_refresh_token)

            # 7. Calculate expiry datetime for the refresh token
            expires_at = refresh_token_expiry_datetime()

            # 8. Store the refresh token in the database
            await self.refresh_repo.create_refresh_token(db, jti = jti_refresh_token, user_id = user.id, hashed_token = hashed, expires_at = expires_at, client_ip = ip, user_agent = user_agent)

            # 9. Log the created refresh token
            logger.info("Refresh token created and stored", extra={"request_by_user_id": user.id, "jti_refresh_token": jti_refresh_token})

            # 10. Return schema
            tokens = TokenPair(access_token = access_token, refresh_token = raw_refresh_token, jti = jti_refresh_token, expires_in = expires_in)

            # 11. Log the successful login
            logger.info("Login successful", extra={"request_by_user_id": user.id})

            return UserAndToken(user = UserRead.model_validate(user), token = tokens)


    async def refresh_with_refresh_token(self, presented_raw: str, presented_jti: UUID | None,
                                         ip: str = None, user_agent: str = None) -> UserAndToken:
        
        ''' Rotate refresh token and issue new access token '''
        
        async with self.uow_factory() as db:

            # If a JTI was provided, prefer lookup by JTI (efficient). Otherwise,
            # lookup by the hashed token value.
            token_row = None
            if presented_jti:
                token_row = await self.refresh_repo.get_refresh_token_by_jti(db, presented_jti)
            else:
                presented_hashed = hash_refresh_token(presented_raw)
                token_row = await self.refresh_repo.get_by_token_hash(db, presented_hashed)

            if not token_row:
                # token no encontrado -> posible reuse / uso inválido
                raise DomainError("Invalid refresh token")

            # comprobar expirado o revocado (use timezone-aware now)
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            token_expires = token_row.expires_at
            # Ensure token_expires is timezone-aware for safe compare
            if token_expires.tzinfo is None:
                # assume UTC if DB stored naive datetimes
                token_expires = token_expires.replace(tzinfo=timezone.utc)

            if token_row.revoked or token_expires < now:
                # posible reuse/compromiso
                # por seguridad: revocar todos del usuario
                await self.refresh_repo.revoke_all_refresh_tokens_for_user(db, token_row.user_id)
                raise DomainError("Refresh token invalid or expired")

            # comprobar hash coincide
            presented_hashed = hash_refresh_token(presented_raw)
            if not hmac.compare_digest(presented_hashed, token_row.hashed_token):
                # mismatch -> posible reuse
                await self.refresh_repo.revoke_all_refresh_tokens_for_user(db, token_row.user_id)
                raise DomainError("Refresh token invalid (hash mismatch)")

            # OK -> rotar: crear nuevo raw + jti y guardar, marcar viejo revocado->replaced_by
            new_raw, new_jti = generate_raw_refresh_token()
            new_hashed = hash_refresh_token(new_raw)
            new_expires_at = refresh_token_expiry_datetime()

            await self.refresh_repo.create_refresh_token(db, jti=new_jti, user_id=token_row.user_id, hashed_token=new_hashed, expires_at=new_expires_at, client_ip=ip, user_agent=user_agent)
            await self.refresh_repo.mark_refresh_token_replaced(db, old_jti=token_row.jti, new_jti=new_jti)

            # crear nuevo access token
            user = await self.user_repo.get_by_id(db, token_row.user_id)
            role_names = [r.name for r in user.roles] if getattr(user, 'roles', None) else []
            token_info = create_user_access_token(subject=str(user.id), roles=role_names, is_superuser=user.is_superuser)
            access_token = token_info.access_token
            expires_in = token_info.expires_in

            # opcional: actualizar last_used_at with timezone-aware datetime
            await self.refresh_repo.update_refresh_token_last_used(db, jti=new_jti, used_at = datetime.now(timezone.utc))

            return UserAndToken(user = UserRead.model_validate(user), token = TokenPair(access_token = access_token, refresh_token = new_raw, jti = new_jti, expires_in = expires_in))


    async def logout(self, user_id: UUID, jti: UUID):

        '''Logout the user from the token given'''

        # 0. Log the attempt
        logger.info(
            "Logout user",
            extra={
                "request_by_user_id": user_id,
            }
        )

        async with self.uow_factory() as db:

            # 1. Check user exists
            user = await self.user_repo.get_by_id(db, user_id)
            if not user:
                raise NotFoundError(f"User {user_id} not found")
        
            # 2️. Get refresh token
            token = await self.refresh_repo.get_refresh_token_by_jti(db, jti)
            if not token:
                raise NotFoundError(f"Refresh token {jti} not found")
            
            # 3️. Ensure token belongs to the same user
            if token.user_id != user.id:
                raise DomainError("Token does not belong to this user")

            # 4️. Check if token already revoked
            if token.revoked:
                logger.warning(
                    "Attempted to revoke already revoked token",
                    extra={"request_by_user_id": user.id, "jti": jti},
                )

            # 5. Revoke refresh token
            await self.refresh_repo.revoke_refresh_token(db, jti)

            # 6️. Log successful logout
            logger.info(
                "User logged out: refresh token revoked",
                extra={"request_by_user_id": user.id, "jti": jti},
            )


    async def revoke_refresh_token_by_jti(self, jti: UUID) -> None:
       
        """
        Revokes a refresh token using only its JTI
        Used when access token is expired and user_id is unknown
        """

        # Check is uuid
        try:
            jti_a = UUID(jti)
        except Exception:
            raise DomainError("jti malformed - invalid UUID format")

        # 0. Log the attempt
        logger.info(
            "Start revoke refresh token by JTI",
            extra={
                "refresh_jti": jti,
            }
        )

        async with self.uow_factory() as db:
            
            # 1. Check refresh token exists
            token = await self.refresh_repo.get_refresh_token_by_jti(db, jti)
            
            if not token:
                logger.info("Refresh token given not found")
                return

            # 2. If revoked, dont do anything
            if token.revoked:
                logger.info("Token given was already revoked", extra={"request_by_user_id": token.user_id, "jti": token.jti})
                return
            
            # 3. Revoke refresh token
            await self.refresh_repo.revoke_refresh_token(db, jti)

            # 4. Log successful logout
            logger.info(
                "Refresh token revoked by JTI",
                extra={"request_by_user_id": token.user_id, "jti": jti},
            )


    async def logout_all_devices(self, user_id: UUID):

        '''Revoke all the refresh tokens for a given user (log out from all devices)'''

        # 0. Log the attempt
        logger.info(
            "Log out from all devices",
            extra={
                "request_by_user_id": user_id,
            }
        )

        async with self.uow_factory() as db:

            # 1. Check user exists
            user = await self.user_repo.get_by_id(db, user_id)
            if not user:
                raise NotFoundError(f"User {user_id} not found")

            #2. Log out
            await self.refresh_repo.revoke_all_refresh_tokens_for_user(db, user_id)

            # 3. Log successful logout
            logger.info("Successful log out from all devices", extra={"request_by_user_id": user_id})


    async def revoke_refresh_token_by_raw(self, raw_token: str):

        """
        Revokes a refresh token using only its raw token value
        """

        # 0. Log the attempt
        logger.info("Start revoke refresh token by RAW")

        async with self.uow_factory() as db:
            
            # 1. Hash raw token and check if exists
            hashed = hash_refresh_token(raw_token)

            token = await self.refresh_repo.get_by_token_hash(db, hashed)
            if not token:
                logger.info("Refresh token given not found")
                return
            
            # 2. If revoked, dont do anything
            if token.revoked:
                logger.info("Token given was already revoked", extra={"request_by_user_id": token.user_id, "jti": token.jti})
                return
            
            # 3. Revoke refresh token
            await self.refresh_repo.revoke_refresh_token(db, token.jti)

            # 4. Log successful revoke
            logger.info(
                "Refresh token revoked by RAW",
                extra={"request_by_user_id": token.user_id, "jti": token.jti},
            )


    async def client_credentials(self, client_id: UUID, client_secret: str) -> TokenPair:

        """Validate client_id/secret and issue an access token."""

        # 0. Log the attempt
        logger.info("Client credentials attempt", extra={"client_id": str(client_id)})

        async with self.uow_factory() as db:

            # 1. Use ClientRepository to find client
            client = await self.client_repo.read_by_clientid(db, client_id)
            
            # 2. Validate client existence and active status
            if not client:
                raise DomainError("Invalid client credentials")
            if not client.is_active:
                logger.info("Client not active", extra={"client_id": str(client_id)})
                raise DomainError("Invalid client credentials")

            # 3. Verify secret
            secret_valid = verify_password(client_secret, client.hashed_secret)
            if not secret_valid:
                logger.info("Invalid secret", extra={"client_id": str(client_id)})
                raise DomainError("Invalid client credentials")

            # 4. Get permissions 
            permissions = [p.name for p in client.permissions] if client.permissions else []

            # 5. Create access token
            token_info = create_client_access_token(subject = str(client.id), permissions = permissions)
            access_token = token_info.access_token
            expires_in = token_info.expires_in

            token_pair = TokenPair(access_token = access_token, refresh_token = None, jti = token_info.jti, expires_in = expires_in)

            logger.info("Client authentication successful", extra={"token_type": token_pair.token_type})

            return token_pair
