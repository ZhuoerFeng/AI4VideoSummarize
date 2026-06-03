"""Video downloader module using yt-dlp."""

import re
import shutil
from pathlib import Path
from yt_dlp import YoutubeDL


def detect_source_type(source: str) -> str:
    """Detect the type of video source.

    Args:
        source: Video source string (path, URL, etc.)

    Returns:
        One of: 'local', 'youtube', 'bilibili', 'url'
    """
    # Local file
    if Path(source).exists():
        return "local"

    # YouTube
    if re.match(r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/", source):
        return "youtube"

    # Bilibili
    if re.match(r"(https?://)?(www\.)?bilibili\.com/", source):
        return "bilibili"

    # Generic URL
    if re.match(r"https?://", source):
        return "url"

    # Assume local path that doesn't exist yet
    raise FileNotFoundError(f"Video source not found: {source}")


def download_video(source: str, output_dir: Path, config: dict) -> Path:
    """Download or copy video to output directory.

    Args:
        source: Video source (local path, URL, or video site link).
        output_dir: Directory to save the video.
        config: Download configuration.

    Returns:
        Path to the video file in output directory.
    """
    source_type = detect_source_type(source)

    if source_type == "local":
        # Copy local file to output directory
        src_path = Path(source)
        dst_path = output_dir / f"video{src_path.suffix}"
        shutil.copy2(src_path, dst_path)
        print(f"[Download] Copied local file: {src_path.name}")
        return dst_path

    # Use yt-dlp for all remote sources
    ydl_opts = {
        "outtmpl": str(output_dir / "video.%(ext)s"),
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "quiet": False,
        "no_warnings": False,
    }

    # Apply proxy if configured
    proxy = config.get("download", {}).get("proxy", "")
    if proxy:
        ydl_opts["proxy"] = proxy

    # Apply cookies if configured
    cookies_file = config.get("download", {}).get("cookies_file", "")
    if cookies_file:
        ydl_opts["cookiefile"] = cookies_file

    print(f"[Download] Downloading from {source_type}: {source}")

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(source, download=True)
        # Get the actual filename
        filename = ydl.prepare_filename(info)
        # yt-dlp may change extension after merge
        video_path = Path(filename)
        if not video_path.exists():
            # Try with .mp4 extension
            video_path = video_path.with_suffix(".mp4")

    if not video_path.exists():
        # Search for any video file in output dir
        for ext in [".mp4", ".mkv", ".webm", ".flv"]:
            candidates = list(output_dir.glob(f"video{ext}"))
            if candidates:
                video_path = candidates[0]
                break

    print(f"[Download] Saved: {video_path.name}")
    return video_path
