from fastapi import APIRouter, Depends, status
from app.services.health import HealthService
from app.dependencies.services import get_health_service
from app.schemas.health import HealthCheckResponse

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=HealthCheckResponse,
    summary="Service health check",
    description="**Check the health status of the backend service only.**",
)
async def health_check(health_service: HealthService = Depends(get_health_service)) -> HealthCheckResponse:
    """Return backend service health summary."""
    return await health_service.check_health()


@router.get(
    "/ready",
    status_code=status.HTTP_200_OK,
    response_model=HealthCheckResponse,
    summary="Readiness check",
    description="**Check the health status of backend dependencies, including the database.**",
)
async def readiness_check(health_service: HealthService = Depends(get_health_service)) -> HealthCheckResponse:
    """Return readiness health summary."""
    return await health_service.check_readiness()
