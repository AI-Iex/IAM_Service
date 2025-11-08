from app.services.interfaces.health import IHealthService
from app.repositories.interfaces.health import IHealthRepository
from app.db.unit_of_work import UnitOfWorkFactory
from app.core.exceptions import NotFoundError
import logging
from datetime import datetime
from app.schemas.health import HealthCheckResponse

logger = logging.getLogger(__name__)


class HealthService(IHealthService):
    def __init__(self, 
                 health_repo: IHealthRepository, 
                 uow_factory: UnitOfWorkFactory):
        
        self._health_repo = health_repo
        self._uow_factory = uow_factory

    async def check_health(self) -> HealthCheckResponse:
        
        """Perform comprehensive health checks."""
        
        async with self._uow_factory() as db:
            
            checks = await self._health_repo.detailed_health_check(db)
            
            all_healthy = all(
                check.status == "healthy" 
                for check in checks.values()
            )
            global_status = "healthy" if all_healthy else "unhealthy"
            
            return HealthCheckResponse(
                status=global_status,
                timestamp=datetime.utcnow(),
                checks=checks
            )
