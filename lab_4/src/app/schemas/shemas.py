from pydantic import BaseModel, EmailStr
from datetime import date


class SUserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
