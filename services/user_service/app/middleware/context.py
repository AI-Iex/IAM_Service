from fastapi import Request
from uuid import uuid4
import logging

from app.core.logging_config import set_request_context, reset_request_context

logger = logging.getLogger("user_service")


async def context_middleware(request: Request, call_next):

    """ Middleware that sets the request_id into contextvars so log filters can inject it  """
   
    request_id = getattr(request.state, "request_id", None)
    if not request_id:
        request_id = str(uuid4())
        request.state.request_id = request_id

    response = await call_next(request)
    return response