import yt_dlp
from pydub import AudioSegment
import os
import tempfile

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# YouTube often blocks cloud servers, and which player client gets through changes
# over time, so try a few in order until one works.
_CLIENT_ATTEMPTS = [None, ["tv", "android_vr"], ["web_safari", "mweb"], ["ios"]]


def _cookie_file():
    """Optional: put the contents of a Netscape cookies.txt in the YT_COOKIES secret."""
    raw = os.getenv("YT_COOKIES")
    if not raw:
        return None
    path = os.path.join(tempfile.gettempdir(), "yt_cookies.txt")
    with open(path, "w") as f:
        f.write(raw)
    return path


def download_youtube_audio(url: str) -> str:
    output_path = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")
    cookies = _cookie_file()
    last_error = None

    for clients in _CLIENT_ATTEMPTS:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
            "quiet": True,
            "noplaylist": True,   # a link with &list=... must not download a whole playlist
            "retries": 3,
        }
        if clients:
            ydl_opts["extractor_args"] = {"youtube": {"player_client": clients}}
        if cookies:
            ydl_opts["cookiefile"] = cookies
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return os.path.splitext(ydl.prepare_filename(info))[0] + ".wav"
        except Exception as e:  # try the next client
            last_error = e
            print(f"YouTube download failed with clients={clients}: {e}")

    raise last_error





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