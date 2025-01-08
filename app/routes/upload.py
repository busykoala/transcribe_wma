from fastapi import APIRouter
from fastapi import Depends
from fastapi import File
from fastapi import UploadFile
from fastapi.responses import HTMLResponse

from app.utils.audio_processing import process_audio
from app.utils.auth_utils import is_authenticated

upload_router = APIRouter()


@upload_router.get("/", response_class=HTMLResponse)
async def upload_form(authenticated: bool = Depends(is_authenticated)):
    with open("app/templates/upload.html") as f:
        return HTMLResponse(content=f.read())


@upload_router.post("/upload/")
async def upload_file(
    file: UploadFile = File(...),
    authenticated: bool = Depends(is_authenticated),
):
    transcription = await process_audio(file)
    with open("app/templates/result.html") as f:
        html_template = f.read()
    return HTMLResponse(
        content=html_template.format(transcription=transcription)
    )
