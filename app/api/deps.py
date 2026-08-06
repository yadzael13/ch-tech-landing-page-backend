import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.errors import UnauthorizedError
from app.core.security import decode_access_token

# auto_error=False: a missing header should surface as our own envelope
# (via UnauthorizedError) rather than FastAPI's default plain 403.
_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> str:
    if credentials is None:
        raise UnauthorizedError("Missing bearer token")

    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedError("Invalid or expired access token") from exc

    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise UnauthorizedError("Invalid access token")
    return subject
