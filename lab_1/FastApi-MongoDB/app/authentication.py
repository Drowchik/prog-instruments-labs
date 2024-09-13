from datetime import datetime, timedelta
import re

import pyotp
from bson import ObjectId
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Response,
    status,
)
from fastapi.responses import JSONResponse

from app.database import client
from app.schemas import (
    CreateUser,
    ForgotPassword,
    LoginUser,
    ResendCode,
    ResponseUser,
    Verification,
)
from app.security import (
    create_jwt_token,
    get_password_hash,
    send_email,
    verify_password,
    jwt_refresh_token_required,
)


# create the user collection
User = client.MarketPlace.users

# the valid username of the user (only alphabets and numbers  and (.)(-) between the chracters) 
username_regex = re.compile(
    r"^(([a-zA-Z0-9]+)|([a-zA-Z0-9]+\.*[a-zA-Z0-9]+)|([a-zA-Z0-9]+-*[a-zA-Z0-9]+))$"
)


auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

# setting the default access and refresh token expires time 
ACCESS_TOKEN_EXPIRES_IN: timedelta = timedelta(hours=1)
REFRESH_TOKEN_EXPIRES_IN: timedelta = timedelta(days=30)


def deserialize_data(user):
    return {"id": str(user["_id"]),
            "name": user["name"],
            "password": user["password"],
            "username": user["username"],
            "is_active": user["is_active"],
            "is_verified": user["is_verified"],
            "otp_secret": user["otp_secret"],
            "email": user["email"]}


@auth_router.post("/signup", 
                  status_code=status.HTTP_201_CREATED, 
                  response_model=ResponseUser)
async def signup(body: CreateUser, background_tasks: BackgroundTasks) -> dict:
    """ 
        Registers a new user by creating an entry in the database.
        
        Args:
            body (CreateUser): pydantic BaseModel, user information
            background_tasks (BackgroundTasks): task queue for background processes.

        Returns:
            _type_: created user's ID and email.
    """
    # checking if the user email exists
    if User.find_one({"email": body.email}):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, 
                            detail="email already exist")
    if User.find_one({"username": body.username}):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, 
                            detail="username already taken")
    if not username_regex.match(body.username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail="invalid username")
    # hashing the password
    body.password = get_password_hash(body.password)
    valid_user = dict(body)
    valid_user["created_at"] = datetime.today()
    valid_user["is_active"] = True
    valid_user["is_verified"] = False

    # generating the on otp code and sending it via email
    otp_base32 = pyotp.random_base32()
    totp = pyotp.TOTP(otp_base32, interval=600)
    verification_code = totp.now()
    background_tasks.add_task(send_email,body.email, verification_code)
    valid_user["otp_secret"] = otp_base32
    new_user = User.insert_one(valid_user)
    response = {"id": str(new_user.inserted_id), "email": body.email}

    return response


@auth_router.post("/verify", status_code=status.HTTP_200_OK)
async def verify(body: Verification, response: Response) -> dict:
    """
        Verifies the user

        Args:
            body (Verification): pydantic BaseModel
            response (Response): HTTP response object to set cookies

        Returns:
            dict: The verified user's ID
    """
    user = User.find_one({"_id": ObjectId(body.id)})
    # checking if the user exists
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="user not found")
    user_data = deserialize_data(user)
    otp_base32 = user_data["otp_secret"]
    totp = pyotp.TOTP(otp_base32, interval=600)

    # verifying if the verification code is correct
    if not totp.verify(body.verification_code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail='please enter a correct verification code')
    # checking if the user is already verified using for password reset
    if user_data["is_verified"]:
        raise JSONResponse(status_code=status.HTTP_200_OK, 
                           detail="user already verified")
    
    User.update_one({"_id": ObjectId(body.id)}, 
                    {"$set": {"is_verified": True}})

    # generating access and refresh token and storing them in cookies
    access_token = await create_jwt_token(data={"id": user_data["id"]}, 
                                          expires_time=ACCESS_TOKEN_EXPIRES_IN, 
                                          mode="access_token")
    refresh_token = await create_jwt_token(data={"id": user_data["id"]}, 
                                           expires_time=REFRESH_TOKEN_EXPIRES_IN, 
                                           mode="refresh_token")

    response.set_cookie(key="access_token", value=access_token, 
                        expires=ACCESS_TOKEN_EXPIRES_IN, 
                        httponly=True,
                        domain=None, 
                        max_age=ACCESS_TOKEN_EXPIRES_IN, 
                        secure=False, 
                        samesite="lax")
    
    response.set_cookie(key="refresh_token", 
                        value=refresh_token,
                        expires=REFRESH_TOKEN_EXPIRES_IN,
                        httponly=True,
                        domain=None,
                        max_age=REFRESH_TOKEN_EXPIRES_IN,
                        secure=False,
                        samesite="lax")
    
    response.set_cookie(key="logged_in",
                        value="True",
                        expires=ACCESS_TOKEN_EXPIRES_IN,
                        domain=None,
                        max_age=ACCESS_TOKEN_EXPIRES_IN,
                        secure=False,
                        httponly=False,
                        samesite="lax")

    return {"id":user_data["id"],
            "type": "Bearer",
            "access_token": access_token, 
            "refresh_token": refresh_token} 


@auth_router.post("/login", status_code=status.HTTP_200_OK)
async def login(body: LoginUser, response: Response) -> dict:
    """
        Authenticates a user by validating the email and password.

        Args:
            body (LoginUser): pydantic BaseModel
            response (Response): The HTTP response object to set cookies.

        Returns:
            dict: The logged-in user
    """
    user=User.find_one({"email": body.email})
    # checking if the user exists
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="user not found")
    user_data = deserialize_data(user)
    # checking if the user is active or verified
    if not user_data["is_verified"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                            detail="user not verified")
    # checking if the password is correct
    if not verify_password(body.password, user_data["password"]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail="invalid password")
    
    # generating access and refresh token and storing them in cookies
    access_token = await create_jwt_token(data={"id":user_data["id"]}, 
                                          expires_time=ACCESS_TOKEN_EXPIRES_IN, 
                                          mode="access_token")  
    refresh_token = await create_jwt_token(data={"id":user_data["id"]}, 
                                           expires_time=REFRESH_TOKEN_EXPIRES_IN,
                                           mode="refresh_token")
    response.set_cookie(key="access_token", 
                        value=access_token, 
                        expires=ACCESS_TOKEN_EXPIRES_IN, 
                        httponly=True,
                        domain=None,
                        max_age=ACCESS_TOKEN_EXPIRES_IN, 
                        secure=False, 
                        samesite="lax")
    
    response.set_cookie(key="refresh_token", 
                        value=refresh_token, 
                        expires=REFRESH_TOKEN_EXPIRES_IN,
                        httponly=True, 
                        domain=None,
                        max_age=REFRESH_TOKEN_EXPIRES_IN,
                        secure=False, 
                        samesite="lax")
    
    response.set_cookie(key="logged_in", 
                        value="True", 
                        expires=ACCESS_TOKEN_EXPIRES_IN, 
                        domain=None,
                        max_age=ACCESS_TOKEN_EXPIRES_IN, 
                        secure=False, 
                        httponly=False, 
                        samesite="lax")

    return {"id": user_data["id"], "type": "Bearer", "access_token": access_token, "refresh_token": refresh_token}


@auth_router.post("/send-code", status_code=status.HTTP_200_OK)
async def resend_code(body: ResendCode, background_tasks: BackgroundTasks) -> dict:
    """
        Resends the verification code to the user's email.

        Args:
            body (ResendCode): Pydantic BaseModel
            background_tasks (BackgroundTasks): Task queue for background processes.

        Returns:
            dict: message
    """
    user = User.find_one({"email": body.email})
    # checking if the user exists
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="user not found")
    user_data = deserialize_data(user)
    # generating the verification code
    otp_base32 = pyotp.random_base32()
    totp = pyotp.TOTP(otp_base32,interval=600)
    verification_code = totp.now()
    User.update_one({"_id": ObjectId(user_data["id"])},
                    {"$set": {"otp_secret": otp_base32}})
    # sending the verification code via email
    background_tasks.add_task(send_email,body.email, verification_code)
    return {"message": "verification code sent to your email"}


@auth_router.patch("/forgot-password", status_code=status.HTTP_200_OK)
async def reset_password(response: Response, body: ForgotPassword) -> dict:
    """
        Resets the user's password.

        Args:
            response (Response): HTTP response object
            body (ForgotPassword): Pydantic BaseModel


        Returns:
            dict: user's ID and new access/refresh tokens
    """
    user = User.find_one({"email": body.email})
    # checking if the user exists
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="user not found")
    # updating the user password
    body.password = get_password_hash(body.password)
    user_mapped = User.update_one({"email": body.email}, 
                                  {"$set": {"password": body.password}})
    user_data = deserialize_data(user_mapped)

    # generating access and refresh token and storing them in cookies
    access_token = await create_jwt_token(data={"id": user_data["id"]}, 
                                          expires_time=ACCESS_TOKEN_EXPIRES_IN, 
                                          mode="access_token")  
    refresh_token = await create_jwt_token(data={"id":user_data["id"]}, 
                                           expires_time=REFRESH_TOKEN_EXPIRES_IN, 
                                           mode="refresh_token")
    response.set_cookie(key="access_token", 
                        value=access_token, 
                        expires=ACCESS_TOKEN_EXPIRES_IN, 
                        httponly=True,
                        domain=None, 
                        max_age=ACCESS_TOKEN_EXPIRES_IN, 
                        secure=False, 
                        samesite="lax")
    
    response.set_cookie(key="refresh_token", 
                        value=refresh_token, 
                        expires=REFRESH_TOKEN_EXPIRES_IN, 
                        httponly=True, 
                        domain=None,
                        max_age=REFRESH_TOKEN_EXPIRES_IN, 
                        secure=False, 
                        samesite="lax")
    
    response.set_cookie(key="logged_in",
                        value="True", 
                        expires=ACCESS_TOKEN_EXPIRES_IN, 
                        domain=None,
                        max_age=ACCESS_TOKEN_EXPIRES_IN, 
                        secure=False, 
                        httponly=False, 
                        samesite="lax")

    return {"id":user_data["id"], 
            "type": "Bearer", 
            "access_token": access_token, 
            "refresh_token": refresh_token}


@auth_router.get("/refresh-token", status_code=status.HTTP_200_OK)
async def refresh_token(response: Response,
                        Authorize: dict=Depends(jwt_refresh_token_required)):
    """
        Refresh token

        Args:
            response (Response): HTTP response object
            Authorize (dict, optional): Defaults to Depends(jwt_refresh_token_required).

        Returns:
            _type_: The users new access/refresh tokens.

    """
    user = User.find_one({"_id": ObjectId(Authorize["id"])})

    # checking if the user exists
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='The user belonging to this token no logger exist')
    user_data = deserialize_data(user)
    access_token = await create_jwt_token(data={"id": user_data["id"]}, 
                                          expires_time=ACCESS_TOKEN_EXPIRES_IN, 
                                          mode="access_token")  
    refresh_token = await create_jwt_token(data={"id": user_data["id"]}, 
                                           expires_time=REFRESH_TOKEN_EXPIRES_IN, 
                                           mode="refresh_token")

    response.set_cookie(key="access_token", 
                        value=access_token, 
                        expires=ACCESS_TOKEN_EXPIRES_IN, 
                        httponly=True,
                        domain=None, 
                        max_age=ACCESS_TOKEN_EXPIRES_IN, 
                        secure=False, 
                        samesite="lax")
    
    response.set_cookie(key="refresh_token", 
                        value=refresh_token, 
                        expires=REFRESH_TOKEN_EXPIRES_IN, 
                        httponly=True, 
                        domain=None,
                        max_age=REFRESH_TOKEN_EXPIRES_IN, 
                        secure=False, 
                        samesite="lax")

    response.set_cookie(key="logged_in",
                        value="True", 
                        expires=ACCESS_TOKEN_EXPIRES_IN, 
                        domain=None,
                        max_age=ACCESS_TOKEN_EXPIRES_IN, 
                        secure=False, httponly=False, 
                        samesite="lax")
    
    return {"type": "Bearer", 
            "access_token": access_token,
            "refresh_token": refresh_token}
    