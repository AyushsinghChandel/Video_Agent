import yt_dlp
from pydub import AudioSegment
import os

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def download_youtube_audio(url: str) -> str:
    output_path = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info).replace('.webm', '.wav').replace('.m4a', '.wav').replace('.mp3', '.wav')
    return filename





def convert_to_wav(input_file: str) -> str:
    """Converts any audio file to WAV format using pydub."""
    output_path = os.path.splitext(input_file)[0] + "_converted.wav"
    audio = AudioSegment.from_file(input_file)
    audio = audio.set_channels(1).set_frame_rate(16000)
    audio.export(output_path, format="wav")
    return output_path




def chunk_audio(wav_path : str, chunk_minutes : int = 10) -> list:
    """Splits a WAV file into chunks of specified duration in minutes."""
    audio = AudioSegment.from_wav(wav_path)
    chunk_length_ms = chunk_minutes * 60 * 1000  # Convert minutes to milliseconds
    chunks = []
    
    for i in range(0, len(audio), chunk_length_ms):
        chunk = audio[i:i + chunk_length_ms]
        chunk_filename = f"{wav_path}_chunk_{i}.wav"
        chunk.export(chunk_filename, format="wav")
        chunks.append(chunk_filename)
    
    return chunks



def process_input(source: str) -> list:
    if source.startswith("http://") or source.startswith("https://"):
        print(f"Downloading audio from YouTube URL: {source}")
        wav_path = download_youtube_audio(source)
    else:
        print(f"Processing local audio file: {source}")
        wav_path = convert_to_wav(source)

    print(f"Chunking audio file...")
    chunks = chunk_audio(wav_path)
    print(f"Audio ready - {len(chunks)} chunks created.")
    return chunks