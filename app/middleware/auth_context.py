from fastapi import Request
from app.core.logging_config import _user_id_ctx, _client_id_ctx
from app.core.security import decode_token
from app.core.enums import AccessTokenType
from uuid import UUID


async def auth_context_middleware(request: Request, call_next):
    """Middleware to extract user ID or client ID from Authorization header and set it in context."""

    auth_header = request.headers.get("Authorization")

    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header.replace("Bearer ", "")
            payload = decode_token(token)
            subject_id_str = payload.sub
            token_type = payload.type

            if subject_id_str:
                subject_id = UUID(subject_id_str)

                # Set context based on token type using enum
                if token_type == AccessTokenType.CLIENT.value:
                    client_token = _client_id_ctx.set(subject_id)
                    request.state.client_id_token = client_token
                    request.state.client_id = subject_id
                else:
                    user_token = _user_id_ctx.set(subject_id)
                    request.state.user_id_token = user_token
                    request.state.user_id = subject_id

        except Exception:
            # Invalid token; proceed without setting context
            pass

    response = await call_next(request)

    # Clean up context variables after request is processed
    if hasattr(request.state, "user_id_token"):
        _user_id_ctx.reset(request.state.user_id_token)
    if hasattr(request.state, "client_id_token"):
        _client_id_ctx.reset(request.state.client_id_token)

    return response
