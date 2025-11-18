from fastapi import Request
from app.core.logging_config import _user_id_ctx
from app.core.security import decode_token


async def auth_context_middleware(request: Request, call_next):
    """Middleware to extract user ID from Authorization header and set it in context."""

    auth_header = request.headers.get("Authorization")

    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header.replace("Bearer ", "")
            payload = decode_token(token)
            user_id_str = payload.sub

            if user_id_str:
                from uuid import UUID

                user_id = UUID(user_id_str)
                user_token = _user_id_ctx.set(user_id)
                request.state.user_id_token = user_token

        except Exception:
            # Invalid token; proceed without setting user_id context
            pass

    response = await call_next(request)

    # Clean up context variable after request is processed
    if hasattr(request.state, "user_id_token"):
        _user_id_ctx.reset(request.state.user_id_token)

    return response
