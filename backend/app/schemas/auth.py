from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class TokenPayload(BaseModel):
    sub: str        # user id (UUID string)
    role: str
    type: str       # "access" | "refresh"
    exp: int
