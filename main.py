
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
from pydub import AudioSegment
import io

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

    input_file = ''.join(random.choices(string.ascii_letters + string.digits, k=20)) + ".webm"
    output_file = "tmp_" + ''.join(random.choices(string.ascii_letters + string.digits, k=20)) + ".wav"

    try:
        audio_bytes = base64.b64decode(base64_audio)
        with open(input_file, "wb") as f:
            f.write(audio_bytes)

        # Use pydub to convert, matching what your teammate did
        audio = AudioSegment.from_file(input_file, format="webm")
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        audio.export(output_file, format="wav")

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
        for path in [input_file, output_file]:
            if path and os.path.exists(path):
                os.remove(path)