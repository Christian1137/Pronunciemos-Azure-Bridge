
import subprocess
from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pronunciationChecking
import os
import base64
import wave
from fastapi.responses import FileResponse # Import this at the top

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
    # 1. Get data from payload
    sentence = data.get('sentence')
    dialect = data.get('dialect')
    base64_audio = data.get('base64_data')

    if not base64_audio:
        raise HTTPException(status_code=400, detail="No audio data provided")

    input_path = os.path.join(os.getcwd(), "upload_raw.wav")
    output_path = os.path.join(os.getcwd(), "azure_ready.wav")

    try:
        # Save the raw data from the browser
        audio_bytes = base64.b64decode(base64_audio)
        with open(input_path, "wb") as f:
            f.write(audio_bytes)

        # USE FFMPEG TO FORCE PCM WAV (16kHz, Mono, 16-bit)
        # This fixes the "Invalid Header" error regardless of what the browser sent
        command = [
            "ffmpeg", "-y", 
            "-i", input_path,
            "-af", "highpass=f=100, lowpass=f=8000, volume=1.5", # Cleans low rumble and boosts speech
            "-ar", "16000", 
            "-ac", "1", 
            "-c:a", "pcm_s16le", 
            output_path
        ]
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Pass the RE-ENCODED file to Azure
        results = pronunciationChecking.correct_pronunciation_azure(
            sentence, 
            output_path, 
            dialect
        )
        return results

    except subprocess.CalledProcessError as e:
        print(f"FFmpeg Error: {e.stderr.decode()}")
        raise HTTPException(status_code=500, detail="Audio conversion failed")
    #finally:
        # 5. Clean up the file so the container doesn't fill up
        #if os.path.exists(output_path):
            #os.remove(output_path)