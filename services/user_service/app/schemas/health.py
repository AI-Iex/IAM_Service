from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Literal

class DependencyHealth(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    response_time_ms: float

class HealthCheckResponse(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    timestamp: datetime
    checks: Dict[str, DependencyHealth]
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "timestamp": "2025-10-31T18:55:54Z",
                "checks": {
                    "database": {"status": "healthy", "response_time": 12.5},
                    "cache": {"status": "healthy", "response_time": 2.1}
                }
            }
        }
    }