from datetime import datetime
from typing import List, Union

from pydantic import BaseModel, EmailStr, Field, StringConstraints


class ReadProduct(BaseModel):
    """ Pydantic scheme for displaying products """
    id: str
    name: str
    description: str
    price: float
    currency: str = Field(max_length=3)
    category: str
    location: str
    condition: str
    is_available: bool
    views: int
    images_url: List[str] = []
    create_at: Union[datetime, None]


class CreateProduct(BaseModel):
    """ Pydantic scheme for creating products """
    name: str
    description: str
    price: float = Field(..., gt=0)
    category: str
    location: str
    condition: str
    currency: str = Field(default="USD", max_length=3)


# user authentication shemas
class CreateUser(BaseModel):
    """ Pydantic scheme for user registration """
    name: str
    username: str = Field(..., max_length=30)
    email: EmailStr = Field(..., max_length=50)
    password: str = Field(..., min_length=8, max_length=64)


class LoginUser(BaseModel):
    """ Pydantic scheme for user login. """
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=64)


class ResponseUser(BaseModel):
    """ Pydantic scheme for responding when requesting user information. """
    id: str
    email: EmailStr = Field(..., max_length=50)


class Verification(BaseModel):
    """ Pydantic scheme for verification code verification. """
    id: str
    verification_code: str


class ResendCode(BaseModel):
    """ Pydantic scheme for resending the verification code. """
    email:EmailStr = Field(..., max_length=50)


class ForgotPassword(BaseModel):
    """Pydantic scheme for password recovery."""
    email:EmailStr = Field(..., max_length=50)
    password:str = Field(..., min_length=8, max_length=64)


class UserProfile(BaseModel):
    """ Pydantic scheme for the user profile """
    name: str
    username: str
    picture: Union[str, None]
    created_at: Union[datetime, None]


class ReadUserProfile(BaseModel):
    """ Pydantic scheme for presenting information about a user's profile. """
    id: str
    name: str
    username: str
    picture: Union[str, None]
    email: Union[EmailStr, None]
    created_at: Union[datetime, None]


class UpdateUserProfile(BaseModel):
    """ Pydantic scheme for updating the user profile. """
    name: str
    username: str
