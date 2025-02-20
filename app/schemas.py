from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional


class EmailSchema(BaseModel):
    email : EmailStr

class Password_reset_schema(BaseModel):
    token:str
    password:str

class UserOut(BaseModel):
    email: EmailStr
    name: str
    emailVerified: bool
    is_two_factor_enabled: bool
    role:str
    image: str
    id: int
    access_token: str| None = None

    class Config:
        orm_mode = True




class User_create(BaseModel):
    email: EmailStr
    password: str| None = None
    name: str
    image: str| None = None
    provider: Optional[str] = None
    emailVerified: Optional[bool] = None


class User_login(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class Token_data(BaseModel):
    id: Optional[int] = None
