from datetime import datetime, timedelta
import logging
from fastapi import Depends, HTTPException, Request
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from src.app.core.database import get_db
from src.app.models import User
from sqlalchemy import select
from src.app.schemas.shemas import SUserRegister
from passlib.context import CryptContext
from src.app.core.config import settings
from src.app.core.logging_config import logger

import jwt


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        logger.debug("UserService initialized")

    async def get_user_by_filter(self, **kwargs) -> User | None:
        result = await self.db.execute(select(User).filter_by(**kwargs))
        return result.scalar()

    async def create_user(self, email, name: str, hashed_password: str) -> User:
        new_user = User(
            email=email,
            name=name,
            hashed_password=hashed_password,
        )
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        logger.info(
            f"User added to the database: {new_user.email} (ID: {new_user.id})")
        return new_user

    async def register_user(self, user_data: SUserRegister) -> User:
        existing_user = await self.get_user_by_filter(email=user_data.email)
        if existing_user:
            logger.error(
                f"Registration failed: Email {user_data.email} already registered")
            raise HTTPException(
                status_code=400, detail="Email already registered")

        auth_service = AuthService()
        logger.info(f"Registering a new user: {user_data.email}")
        return await self.create_user(
            email=user_data.email,
            hashed_password=auth_service.get_password_hash(user_data.password),
            name=user_data.name
        )

    async def login_user(self, user_data: SUserRegister) -> str:
        existing_user = await self.get_user_by_filter(email=user_data.email)
        auth_service = AuthService()
        if not existing_user or not auth_service.verify_password(user_data.password, existing_user.hashed_password):
            logger.error(
                f"Login failed: Email {user_data.email} not registered or wrong password")
            raise HTTPException(status_code=400, detail="Email not registered")
        return auth_service.create_access_token({"sub": str(existing_user.id)})

    async def get_current_user(self, request):
        auth_service = AuthService()
        token = auth_service.get_token(request)
        payload = auth_service.decode_token(token)
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401)
        user = await self.get_user_by_filter(id=int(user_id))
        logger.info(f"Authenticated user ID: {user_id}")
        return user


class AuthService:
    def __init__(self):
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        logger.debug("AuthService initialized")

    def get_token(self, request: Request) -> str:
        token = request.cookies.get("access_token_blog")
        if not token:
            raise HTTPException(status_code=401, detail="No token provided")
        return token

    def decode_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
        except JWTError:
            logger.error("Invalid token")
            raise HTTPException(status_code=401, detail="Invalid token")
        expire = payload.get("exp")
        if not expire or int(expire) < datetime.utcnow().timestamp():
            logger.error("Token expired")
            raise HTTPException(status_code=401, detail="Token expired")
        return payload

    def create_access_token(self, data: dict) -> str:
        logger.info(f"Creating access token for data: {data}")
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=45)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, settings.secret_key, algorithm=settings.algorithm)
        logger.debug(f"Token created: {encoded_jwt[:10]}...")
        return encoded_jwt

    def get_password_hash(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def verify_password(self, password: str, hash_password: str) -> bool:
        return self.pwd_context.verify(password, hash_password)
