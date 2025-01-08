from datetime import timedelta

from dotenv import load_dotenv
from fastapi import APIRouter
from fastapi import Form
from fastapi import HTTPException
from fastapi import Response
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse

from app.utils.auth_utils import SESSION_EXPIRATION_MINUTES
from app.utils.auth_utils import USERS
from app.utils.auth_utils import create_jwt_token

load_dotenv()

auth_router = APIRouter()


@auth_router.get("/login", response_class=HTMLResponse)
async def login_form():
    try:
        with open("app/templates/login.html") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Template not found")


@auth_router.post("/login")
async def login(
    username: str = Form(...),
    password: str = Form(...),
    response: Response = Response(),
):
    if username in USERS and USERS[username] == password:
        token = create_jwt_token(
            data={"sub": username},
            expires_delta=timedelta(minutes=SESSION_EXPIRATION_MINUTES),
        )
        response = RedirectResponse(url="/", status_code=302)
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            samesite="strict",
            secure=True,
            max_age=SESSION_EXPIRATION_MINUTES * 60,
        )
        return response
    return HTMLResponse("Invalid credentials", status_code=401)


@auth_router.get("/logout")
async def logout(response: Response):
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response
