from typing import List

from fastapi_users import schemas

from pydantic import BaseModel, EmailStr


class UserRead(schemas.BaseUser[int]):
    id: int
    username: str
    email: EmailStr

    class Config:
        from_attributes = True


class UserCreate(schemas.BaseUserCreate):
    username: str
    email: EmailStr
    password: str
    # is_active: Optional[bool] = True
    # is_superuser: Optional[bool] = False
    # is_verified: Optional[bool] = False


class UserUpdate(schemas.BaseUserUpdate):
    username: str
    email: EmailStr
    password: str


class GetUser(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        from_attributes = True


class ListUsers(BaseModel):
    status: str
    results: int
    users: List[GetUser]

