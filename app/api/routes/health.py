from fastapi import APIRouter, Depends, status
from app.services.health import HealthService
from app.dependencies.services import get_health_service
from app.schemas.health import HealthCheckResponse

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=HealthCheckResponse,
    summary="Health check",
    description="**Check the health status of the service and its dependencies.**",
)
async def health_check(health_service: HealthService = Depends(get_health_service)) -> HealthCheckResponse:
    """Return service health summary."""
    return await health_service.check_health()
