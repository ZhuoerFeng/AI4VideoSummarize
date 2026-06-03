"""Audio extraction module using ffmpeg."""

import subprocess
import shutil
from pathlib import Path


def check_ffmpeg():
    """Check if ffmpeg is available."""
    if not shutil.which("ffmpeg"):
        raise RuntimeError(
            "ffmpeg not found. Please install ffmpeg:\n"
            "  Ubuntu/Debian: sudo apt install ffmpeg\n"
            "  macOS: brew install ffmpeg\n"
            "  Windows: https://ffmpeg.org/download.html"
        )


def extract_audio(video_path: Path, output_dir: Path, format: str = "mp3") -> Path:
    """Extract audio from video file.

    Args:
        video_path: Path to the video file.
        output_dir: Directory to save extracted audio.
        format: Audio format (mp3, wav, etc.)

    Returns:
        Path to the extracted audio file.
    """
    check_ffmpeg()

    audio_path = output_dir / f"audio.{format}"

    print(f"[Audio] Extracting audio from: {video_path.name}")

    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-vn",                    # No video
        "-acodec", "libmp3lame" if format == "mp3" else "pcm_s16le",
        "-ar", "16000",           # 16kHz sample rate (good for speech)
        "-ac", "1",               # Mono
        "-y",                     # Overwrite
        str(audio_path),
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{result.stderr}")

    print(f"[Audio] Extracted: {audio_path.name} ({audio_path.stat().st_size / 1024 / 1024:.1f} MB)")
    return audio_path
