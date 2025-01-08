import base64
import os
from io import BytesIO
from tempfile import NamedTemporaryFile

import requests
from pydub import AudioSegment


def _prepare_payload(audio_bytes):
    audio = AudioSegment.from_file(BytesIO(audio_bytes), format="wav")
    buffered = BytesIO()
    audio.export(buffered, format="wav")
    encoded_audio = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return {"inputs": encoded_audio}


def remote_pipeline(payload):
    api_url = (
        "https://api-inference.huggingface.co/models/openai/whisper-medium"
    )
    headers = {
        "Authorization": f"Bearer {os.getenv('HUGGINGFACEHUB_API_TOKEN')}"
    }
    response = requests.post(api_url, headers=headers, json=payload)
    return response.json()


async def process_audio(file):
    with (
        NamedTemporaryFile(delete=False, suffix=".wma") as temp_input,
        NamedTemporaryFile(delete=False, suffix=".wav") as temp_output,
    ):
        try:
            temp_input.write(await file.read())
            temp_input.flush()
            temp_input_path = temp_input.name
            temp_output_path = temp_output.name

            audio = AudioSegment.from_file(temp_input_path)
            audio.export(temp_output_path, format="wav")

            with open(temp_output_path, "rb") as f:
                wav_bytes = f.read()

            payload = _prepare_payload(wav_bytes)
            result = remote_pipeline(payload)
            return result.get("text", "Error: No transcription available")
        finally:
            os.remove(temp_input_path)
            os.remove(temp_output_path)
