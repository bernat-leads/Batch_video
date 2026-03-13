"""Auth request/response schemas."""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    password: str


class AuthStatus(BaseModel):
    authenticated: bool
