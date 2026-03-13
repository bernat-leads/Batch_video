"""Auth routes — login, logout, session check."""

import hmac

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from api.auth.schemas import AuthStatus, LoginRequest
from api.deps.auth import AuthDep, SerializerDep, create_session_cookie
from api.settings import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(body: LoginRequest, serializer: SerializerDep) -> AuthStatus:
    """Verify password and set signed session cookie."""
    if not hmac.compare_digest(body.password, settings.APP_PASSWORD):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password",
        )

    token = create_session_cookie(serializer, {"authenticated": True})

    response = JSONResponse(content={"authenticated": True})
    response.set_cookie(
        key="session",
        value=token,
        httponly=True,
        secure=settings.ENVIRONMENT != "local",
        samesite="lax",
        path="/",
        max_age=settings.SESSION_MAX_AGE,
    )
    return response


@router.post("/logout")
def logout() -> AuthStatus:
    """Clear session cookie."""
    response = JSONResponse(content={"authenticated": False})
    response.delete_cookie(key="session", path="/")
    return response


@router.get("/me")
def me(_auth: AuthDep) -> AuthStatus:
    """Check if current session is valid."""
    return AuthStatus(authenticated=True)
