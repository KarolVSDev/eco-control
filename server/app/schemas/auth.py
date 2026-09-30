from pydantic import (
    BaseModel,
    EmailStr,
    Field,
)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(
        min_length=1,
        max_length=100,
    )

    new_password: str = Field(
        min_length=6,
        max_length=100,
    )


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut