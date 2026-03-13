"""Authentication dependencies — serializer + session validation via DI."""

from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from api.settings import settings


def get_serializer() -> URLSafeTimedSerializer:
    """Provide a URLSafeTimedSerializer configured with the app secret key."""
    return URLSafeTimedSerializer(settings.SECRET_KEY)


SerializerDep = Annotated[URLSafeTimedSerializer, Depends(get_serializer)]


def get_current_session(
    serializer: SerializerDep,
    session: str | None = Cookie(default=None),
) -> dict:
    """Validate the signed session cookie.

    Raises 401 if the cookie is missing, expired, or tampered with.
    """
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    try:
        data: dict = serializer.loads(session, max_age=settings.SESSION_MAX_AGE)
    except SignatureExpired:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired",
        )
    except BadSignature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session",
        )
    return data


AuthDep = Annotated[dict, Depends(get_current_session)]


def create_session_cookie(
    serializer: URLSafeTimedSerializer,
    data: dict,
) -> str:
    """Sign and return a session cookie value."""
    return serializer.dumps(data)
