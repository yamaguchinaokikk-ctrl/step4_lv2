from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    staff_id: str = Field(..., min_length=4, max_length=12)
    password: str = Field(..., min_length=8, max_length=16)


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    staff_id: str
    staff_name: str | None = None


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class LogoutRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


class SessionResponse(BaseModel):
    staff_id: str
    staff_name: str | None = None
