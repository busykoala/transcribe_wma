import os
from datetime import datetime
from datetime import timedelta

import jwt
from dotenv import load_dotenv
from fastapi import HTTPException
from fastapi.requests import Request

load_dotenv()

USERS = {"admin": os.getenv("PASSWORD")}
SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")
ALGORITHM = "HS256"
SESSION_EXPIRATION_MINUTES = 30


def create_jwt_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_jwt_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid session")


async def is_authenticated(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=303, detail="Redirect", headers={"Location": "/login"}
        )

    verify_jwt_token(token)
    return True
