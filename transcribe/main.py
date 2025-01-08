import base64
import os
from io import BytesIO
from tempfile import NamedTemporaryFile

import requests
from dotenv import load_dotenv
from fastapi import Depends
from fastapi import FastAPI
from fastapi import File
from fastapi import Form
from fastapi import HTTPException
from fastapi import Request
from fastapi import Response
from fastapi import UploadFile
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from pydub import AudioSegment
from pydub.utils import which

load_dotenv()

app = FastAPI()
model = "openai/whisper-medium"

# Simulated user database
users = {"admin": os.getenv("PASSWORD")}

# Session management
sessions = {}


# Login page
@app.get("/login", response_class=HTMLResponse)
async def login_form():
    return """
    <!doctype html>
    <html>
        <head>
            <title>Login</title>
        </head>
        <body>
            <h1>Login</h1>
            <form action="/login" method="post">
                Username: <input type="text" name="username"><br>
                Password: <input type="password" name="password"><br>
                <button type="submit">Login</button>
            </form>
        </body>
    </html>
    """


@app.post("/login")
async def login(
    username: str = Form(...),
    password: str = Form(...),
    response: Response = Response(),
):
    if username in users and users[username] == password:
        sessions[username] = True
        response = RedirectResponse(url="/", status_code=302)
        response.set_cookie(key="username", value=username)
        return response
    return HTMLResponse("Invalid credentials", status_code=401)


# Dependency to check authentication
async def is_authenticated(request: Request):
    username = request.cookies.get("username")
    if username in sessions and sessions[username]:
        return True
    raise HTTPException(
        status_code=303, detail="Redirect", headers={"Location": "/login"}
    )


# Prepare payload for API call
def _prepare_payload(audio_bytes):
    audio = AudioSegment.from_file(BytesIO(audio_bytes), format="wav")
    buffered = BytesIO()
    audio.export(buffered, format="wav")
    encoded_audio = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return {"inputs": encoded_audio}


# Remote pipeline for API inference
def remote_pipeline(payload):
    api_url = f"https://api-inference.huggingface.co/models/{model}"
    headers = {
        "Authorization": f"Bearer {os.getenv('HUGGINGFACEHUB_API_TOKEN')}"
    }
    response = requests.post(api_url, headers=headers, json=payload)
    return response.json()


@app.get("/", response_class=HTMLResponse)
async def upload_form(authenticated: bool = Depends(is_authenticated)):
    return """
    <!doctype html>
    <html>
        <head>
            <title>Upload WMA File</title>
        </head>
        <body>
            <h1>Upload WMA File</h1>
            <form action="/upload/" method="post" enctype="multipart/form-data">
                <input type="file" name="file">
                <button type="submit">Upload</button>
            </form>
            <br>
            <a href="/logout">Logout</a>
        </body>
    </html>
    """


@app.post("/upload/")
async def upload_file(
    file: UploadFile = File(...),
    authenticated: bool = Depends(is_authenticated),
):
    # Explicitly set ffmpeg and ffprobe path for pydub
    AudioSegment.converter = which("ffmpeg")
    AudioSegment.ffprobe = which("ffprobe")

    # Save uploaded file temporarily
    with (
        NamedTemporaryFile(delete=False, suffix=".wma") as temp_input,
        NamedTemporaryFile(delete=False, suffix=".wav") as temp_output,
    ):
        try:
            # Write uploaded WMA file
            temp_input.write(await file.read())
            temp_input.flush()
            temp_input_path = temp_input.name
            temp_output_path = temp_output.name

            # Log paths for debugging
            print(f"Temp input: {temp_input_path}")
            print(f"Temp output: {temp_output_path}")

            # Convert WMA to WAV using ffmpeg
            audio = AudioSegment.from_file(temp_input_path)
            audio.export(temp_output_path, format="wav")

            # Read the converted WAV bytes
            with open(temp_output_path, "rb") as f:
                wav_bytes = f.read()

            # Process the audio file
            payload = _prepare_payload(wav_bytes)
            result = remote_pipeline(payload)
            transcription = result.get(
                "text", "Error: No transcription available"
            )

            # Return transcription result
            return HTMLResponse(
                content=f"""
            <!doctype html>
            <html>
                <head>
                    <title>Transcription Result</title>
                </head>
                <body>
                    <h1>Transcription Result</h1>
                    <textarea rows="10" cols="50">{transcription}</textarea>
                    <br>
                    <a href="/">Upload another file</a>
                </body>
            </html>
            """,
                status_code=200,
            )

        finally:
            # Ensure temporary files are deleted
            os.remove(temp_input_path)
            os.remove(temp_output_path)


@app.get("/logout")
async def logout(response: Response, request: Request):
    username = request.cookies.get("username")
    if username in sessions:
        del sessions[username]
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("username")
    return response
