from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models import User
from src.app.core.database import get_db
from src.app.schemas.shemas import SUserRegister
from src.app.services.auth import UserService


router = APIRouter(prefix="/auth", tags=["Auth & Пользователи"],)


@router.post("/register")
async def register_user(user_data: SUserRegister, db: AsyncSession = Depends(get_db)):
    user_service = UserService(db)
    user = await user_service.register_user(user_data)
    return user


@router.post("/login")
async def login_user(response: Response, user_data: SUserRegister, db: AsyncSession = Depends(get_db)):
    user_service = UserService(db)
    token = await user_service.login_user(user_data)
    response.set_cookie("access_token_blog", token, httponly=True)


@router.post("/logout")
async def logout_user(response: Response):
    response.delete_cookie("access_token_blog")
    return {"message": "Logged out successfully."}


@router.get("/me")
async def read_users_me(request: Request, db: AsyncSession = Depends(get_db)):
    user_service = UserService(db)
    return await user_service.get_current_user(request)
