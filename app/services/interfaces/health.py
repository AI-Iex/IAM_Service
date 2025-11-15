from abc import ABC, abstractmethod
from app.schemas.health import HealthCheckResponse


class IHealthService(ABC):
    @abstractmethod
    async def check_health(self) -> HealthCheckResponse:
        """Return a health summary"""
        pass
