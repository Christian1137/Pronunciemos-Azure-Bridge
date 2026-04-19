
import subprocess
from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pronunciationChecking
import os
import base64
import wave
from fastapi.responses import FileResponse # Import this at the top
import librosa
import soundfile as sf
import string
import random

app = FastAPI()

origins = [
    "http://localhost:3002",  
    "http://127.0.0.1:3002",
    "http://chdr.cs.ucf.edu:3002",
    "https://chdr.cs.ucf.edu", 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True, 
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.post("/analyze")
async def analyze_audio(data: dict = Body(...)):
    sentence = data.get('sentence')
    dialect = data.get('dialect')
    base64_audio = data.get('base64_data')

    if not base64_audio:
        raise HTTPException(status_code=400, detail="No audio data provided")

    input_file = ''.join(random.choices(string.ascii_letters + string.digits, k=20)) + ".webm"
    output_file = "tmp_" + ''.join(random.choices(string.ascii_letters + string.digits, k=20)) + ".wav"

    try:
        audio_bytes = base64.b64decode(base64_audio)
        with open(input_file, "wb") as f:
            f.write(audio_bytes)

        # FFmpeg just for format conversion, no filters
        command = [
            "ffmpeg", "-y",
            "-i", input_file,
            "-ar", "16000",
            "-ac", "1",
            "-c:a", "pcm_s16le",
            output_file
        ]
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        results = pronunciationChecking.correct_pronunciation_azure(
            sentence,
            output_file,
            dialect
        )
        return results

    except subprocess.CalledProcessError as e:
        print(f"FFmpeg Error: {e.stderr.decode()}")
        raise HTTPException(status_code=500, detail="Audio conversion failed")
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")

    finally:
        for path in [input_file, output_file]:
            if path and os.path.exists(path):
                os.remove(path)