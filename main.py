from dotenv import load_dotenv
from fastapi import FastAPI

from app.routes.auth import auth_router
from app.routes.upload import upload_router

from fastapi.staticfiles import StaticFiles


load_dotenv()

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth_router)
app.include_router(upload_router)
