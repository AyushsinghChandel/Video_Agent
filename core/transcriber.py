import whisper
import os

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small") 

_model = None

def load_model():
    global _model
    if _model is None:
        print(f"Loading Whisper model: {WHISPER_MODEL}")
        _model = whisper.load_model(WHISPER_MODEL)
    return _model

def transcribe_chunk(chunk_path: str, translate: bool = False) -> str:
    model = load_model()
    task = "translate" if translate else "transcribe"
    result = model.transcribe(chunk_path, task=task)
    return result['text']

def transcribe_all(chunks: list, translate: bool = False) -> str:
    full_transcription = ""
    for chunk in chunks:
        print(f"Transcribing chunk: {chunk}")
        transcription = transcribe_chunk(chunk, translate)
        full_transcription += transcription + " "
    return full_transcription