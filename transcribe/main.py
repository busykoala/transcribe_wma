import base64
import os
import subprocess
from io import BytesIO

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


# Convert WMA to WAV if necessary
def convert_to_wav(input_path, output_path):
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-ar",
        "16000",
        "-ac",
        "1",
        output_path,
    ]
    subprocess.run(cmd, check=True)


# Prepare payload for API call
def _prepare_payload(audio_path):
    audio = AudioSegment.from_file(audio_path, format="wav")
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
    input_path = f"./assets/{file.filename}"
    output_path = "./assets/sample.wav"

    # Save uploaded file
    with open(input_path, "wb") as f:
        f.write(await file.read())

    # Convert to WAV
    convert_to_wav(input_path, output_path)

    # Process audio
    payload = _prepare_payload(output_path)
    result = remote_pipeline(payload)
    transcription = result.get("text", "Error: No transcription available")

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


@app.get("/logout")
async def logout(response: Response, request: Request):
    username = request.cookies.get("username")
    if username in sessions:
        del sessions[username]
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("username")
    return response
