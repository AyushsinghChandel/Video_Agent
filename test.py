from utils.audio_processor import process_input
from core.transcriber import transcribe_all

source = "https://www.youtube.com/watch?v=vE57fPUAQh0"

chunks = process_input(source)
transcription = transcribe_all(chunks, translate=False)
print("Final Transcription:")
print(transcription)