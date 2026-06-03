"""Speech-to-text transcription module using Whisper API."""

import math
from pathlib import Path
from openai import OpenAI
from pydub import AudioSegment


# Whisper API limit: 25MB
MAX_CHUNK_SIZE_MB = 24
MAX_CHUNK_SIZE_BYTES = MAX_CHUNK_SIZE_MB * 1024 * 1024


def split_audio(audio_path: Path, output_dir: Path, max_size_mb: int = MAX_CHUNK_SIZE_MB) -> list[Path]:
    """Split audio file into chunks if it exceeds API size limit.

    Args:
        audio_path: Path to the audio file.
        output_dir: Directory to save chunks.
        max_size_mb: Maximum chunk size in MB.

    Returns:
        List of paths to audio chunks.
    """
    file_size = audio_path.stat().st_size

    if file_size <= MAX_CHUNK_SIZE_BYTES:
        return [audio_path]

    print(f"[Transcribe] Audio too large ({file_size / 1024 / 1024:.1f} MB), splitting...")

    audio = AudioSegment.from_file(str(audio_path))
    duration_ms = len(audio)

    # Estimate number of chunks needed
    num_chunks = math.ceil(file_size / MAX_CHUNK_SIZE_BYTES)
    chunk_duration_ms = duration_ms // num_chunks

    chunks = []
    for i in range(num_chunks):
        start = i * chunk_duration_ms
        end = min((i + 1) * chunk_duration_ms, duration_ms)
        chunk = audio[start:end]

        chunk_path = output_dir / f"audio_chunk_{i:03d}.mp3"
        chunk.export(str(chunk_path), format="mp3")
        chunks.append(chunk_path)

    print(f"[Transcribe] Split into {len(chunks)} chunks")
    return chunks


def transcribe_audio(audio_path: Path, output_dir: Path, config: dict) -> str:
    """Transcribe audio using Whisper API.

    Args:
        audio_path: Path to the audio file.
        output_dir: Directory to save chunks if needed.
        config: Whisper API configuration.

    Returns:
        Full transcript text.
    """
    whisper_config = config.get("whisper", {})
    base_url = whisper_config.get("base_url", "https://api.openai.com/v1")
    api_key = whisper_config.get("api_key", "")
    model = whisper_config.get("model", "whisper-1")

    if not api_key:
        raise ValueError("Whisper API key not configured. Please set it in config.yaml.")

    client = OpenAI(base_url=base_url, api_key=api_key)

    # Split audio if needed
    chunks = split_audio(audio_path, output_dir)

    transcripts = []
    for i, chunk_path in enumerate(chunks):
        if len(chunks) > 1:
            print(f"[Transcribe] Processing chunk {i + 1}/{len(chunks)}...")
        else:
            print(f"[Transcribe] Transcribing audio...")

        with open(chunk_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model=model,
                file=audio_file,
                response_format="text",
            )

        transcripts.append(response)

    full_transcript = "\n".join(transcripts)
    print(f"[Transcribe] Done. Total length: {len(full_transcript)} characters")
    return full_transcript


def transcribe_with_timestamps(audio_path: Path, output_dir: Path, config: dict) -> tuple[str, str]:
    """Transcribe audio with timestamps (SRT format).

    Args:
        audio_path: Path to the audio file.
        output_dir: Directory to save chunks if needed.
        config: Whisper API configuration.

    Returns:
        Tuple of (plain text transcript, SRT formatted transcript).
    """
    whisper_config = config.get("whisper", {})
    base_url = whisper_config.get("base_url", "https://api.openai.com/v1")
    api_key = whisper_config.get("api_key", "")
    model = whisper_config.get("model", "whisper-1")

    if not api_key:
        raise ValueError("Whisper API key not configured. Please set it in config.yaml.")

    client = OpenAI(base_url=base_url, api_key=api_key)
    print(f"[Transcribe] OpenAI client initialized with base URL: {base_url}")

    # For SRT, we don't split (may lose sync); fall back to plain if too large
    file_size = audio_path.stat().st_size
    if file_size > MAX_CHUNK_SIZE_BYTES:
        print("[Transcribe] Audio too large for SRT mode, using plain text with chunking...")
        plain = transcribe_audio(audio_path, output_dir, config)
        return plain, ""

    print(f"[Transcribe] Transcribing with timestamps...")

    with open(audio_path, "rb") as audio_file:
        srt_response = client.audio.transcriptions.create(
            model=model,
            file=audio_file,
            response_format="srt",
        )

    with open(audio_path, "rb") as audio_file:
        text_response = client.audio.transcriptions.create(
            model=model,
            file=audio_file,
            response_format="text",
        )

    return text_response, srt_response
