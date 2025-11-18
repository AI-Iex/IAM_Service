from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.repositories.interfaces.health import IHealthRepository
from app.schemas.health import DependencyHealth
from app.core.exceptions import RepositoryError
import time
from typing import Dict, Tuple

class HealthRepository(IHealthRepository):

    async def ping(self, db: AsyncSession) -> Tuple[bool, float]:

        """Perform a light DB check with timing."""

        try:
            start_time = time.time()
            await db.execute(text("SELECT 1"))
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            return True, round(response_time, 2)
        except Exception:
            return False, 0.0
    
    async def detailed_health_check(self, db: AsyncSession) -> Dict[str, DependencyHealth]:
        
        """Perform detailed health checks with metrics."""

        checks = {}
        
        # Database check
        db_status, db_response_time = await self.ping(db)
        checks["database"] = DependencyHealth(
            status = "healthy" if db_status else "unhealthy",
            response_time_ms = db_response_time
        )
        
        # checks["redis"] = await self._check_redis()
        # checks["disk"] = await self._check_disk_space()
        
        return checks
