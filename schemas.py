from pydantic import BaseModel, EmailStr
from typing import List, Optional


class UserBase(BaseModel):
    name: str
    age: int
    gender: str
    email: EmailStr
    city: str
    interests: List[str]

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    email: Optional[EmailStr] = None
    city: Optional[str] = None
    interests: Optional[List[str]] = None


class User(UserBase):
    id: int
    version: int

    class Config:
        orm_mode = True

