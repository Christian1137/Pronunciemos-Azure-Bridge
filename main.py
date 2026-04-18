
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


@app.get("/")
async def root():
    return {"message": "Pronunciemos Azure Bridge API is running"}
    
# Add this new endpoint
@app.get("/download-audio")
async def download_audio():
    # Path to the file FFmpeg created
    file_path = os.path.join(os.getcwd(), "azure_ready.wav")
    
    if os.path.exists(file_path):
        # This will trigger a download in your browser
        return FileResponse(path=file_path, filename="debug_audio.wav", media_type='audio/wav')
    
    raise HTTPException(status_code=404, detail="No audio file found. Try practicing a word first.")

@app.post("/analyze")
async def analyze_audio(data: dict = Body(...)):
    sentence = data.get('sentence')
    dialect = data.get('dialect')
    base64_audio = data.get('base64_data')

    if not base64_audio:
        raise HTTPException(status_code=400, detail="No audio data provided")

    # Use random filenames to avoid collisions if multiple requests come in simultaneously
    input_file = ''.join(random.choices(string.ascii_letters + string.digits, k=20)) + ".webm"
    output_file = "tmp_" + ''.join(random.choices(string.ascii_letters + string.digits, k=20)) + ".wav"

    try:
        audio_bytes = base64.b64decode(base64_audio)
        with open(input_file, "wb") as f:
            f.write(audio_bytes)

        # Match exactly what testing branch was doing
        audio, sampling_rate = librosa.load(input_file, sr=16000, mono=True, duration=30.0)
        sf.write(output_file, audio, 16000)

        results = pronunciationChecking.correct_pronunciation_azure(
            sentence,
            output_file,
            dialect
        )
        return results

    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")

    finally:
        # Clean up temp files
        for path in [input_file, output_file]:
            if path and os.path.exists(path):
                os.remove(path)
