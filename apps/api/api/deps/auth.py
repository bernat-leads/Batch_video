"""Authentication for FastAPI using Bearer JWT from Better Auth."""

from functools import lru_cache
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request
from jwt import PyJWKClient, PyJWKClientError
from jwt.exceptions import DecodeError, ExpiredSignatureError, InvalidAudienceError
from pydantic import BaseModel, ConfigDict

from api.settings import settings


class User(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    email: str
    name: str | None = None
    image: str | None = None


@lru_cache
def get_jwks_client() -> PyJWKClient:
    return PyJWKClient(str(settings.OAUTH_PROVIDER_JWKS_URL), cache_keys=True)


async def get_user(
    request: Request,
    jwks_client: PyJWKClient = Depends(get_jwks_client),
) -> User:
    """Validate Bearer JWT and return user."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Missing or invalid Authorization header"
        )

    token = auth_header[7:].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["EdDSA", "RS256", "ES256"],
            issuer=str(settings.OAUTH_ISSUER_URL),
            audience=str(settings.OAUTH_AUDIENCE),
            options={"verify_aud": True, "verify_iss": True, "verify_exp": True},
        )
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except (DecodeError, InvalidAudienceError, PyJWKClientError) as e:
        raise HTTPException(status_code=401, detail="Invalid token") from e

    try:
        return User.model_validate(payload)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token payload")


AuthenticatedUserDep = Annotated[User, Depends(get_user)]
