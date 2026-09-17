from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(min_length=6, max_length=100)
    role: Literal["admin", "analyst"] = "analyst"
    active: bool = True


class UserResponse(BaseModel):
    id: str
    full_name: str
    email: str
    role: str
    active: bool