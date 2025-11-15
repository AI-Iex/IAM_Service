from sqlalchemy.ext.asyncio import AsyncSession
from abc import ABC, abstractmethod
from typing import Dict, Tuple
from sqlalchemy import text
import time
from app.schemas.health import DependencyHealth

class IHealthRepository(ABC):
    @abstractmethod
    async def ping(self, db: AsyncSession) -> Tuple[bool, float]:
        """Perform a light DB check returning (status, response_time_ms)."""
        pass
    
    @abstractmethod
    async def detailed_health_check(self, db: AsyncSession) -> Dict[str, DependencyHealth]:
        """Perform detailed health checks with metrics."""
        pass