"""Main pipeline orchestration module."""

import time
from pathlib import Path
from datetime import datetime

from .downloader import download_video
from .audio_extractor import extract_audio
from .transcriber import transcribe_audio, transcribe_with_timestamps
from .summarizer import summarize_text


def generate_task_id(source: str) -> str:
    """Generate a unique task ID based on source and timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Create a short identifier from the source
    source_id = Path(source).stem if Path(source).exists() else source.split("/")[-1][:30]
    # Clean up special characters
    source_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in source_id)
    return f"{timestamp}_{source_id}"


def run_pipeline(
    source: str,
    config: dict,
    output_base: str = None,
    skip_summary: bool = False,
    keep_video: bool = True,
) -> Path:
    """Run the full video summarization pipeline.

    Args:
        source: Video source (path, URL, or video site link).
        config: Full configuration dictionary.
        output_base: Base output directory. If None, uses config value.
        skip_summary: If True, only transcribe without summarizing.
        keep_video: If True, keep downloaded video in output.

    Returns:
        Path to the output directory.
    """
    start_time = time.time()

    # Setup output directory
    if output_base is None:
        output_base = config.get("output", {}).get("base_dir", "./output")
    output_base = Path(output_base)
    output_base.mkdir(parents=True, exist_ok=True)

    task_id = generate_task_id(source)
    task_dir = output_base / task_id
    task_dir.mkdir(parents=True, exist_ok=True)

    print(f"{'=' * 60}")
    print(f"AI4VideoSummarize")
    print(f"{'=' * 60}")
    print(f"Source: {source}")
    print(f"Output: {task_dir}")
    print(f"{'=' * 60}")

    # Step 1: Download/copy video
    print(f"\n[Step 1/4] Getting video...")
    video_path = download_video(source, task_dir, config)

    # Step 2: Extract audio
    print(f"\n[Step 2/4] Extracting audio...")
    audio_path = extract_audio(video_path, task_dir)

    # Step 3: Transcribe
    print(f"\n[Step 3/4] Transcribing...")
    transcript, srt = transcribe_with_timestamps(audio_path, task_dir, config)

    # Save transcript
    transcript_path = task_dir / "transcript.txt"
    transcript_path.write_text(transcript, encoding="utf-8")
    print(f"[Step 3/4] Saved: transcript.txt")

    if srt:
        srt_path = task_dir / "transcript.srt"
        srt_path.write_text(srt, encoding="utf-8")
        print(f"[Step 3/4] Saved: transcript.srt")

    # Step 4: Summarize
    if not skip_summary:
        print(f"\n[Step 4/4] Summarizing...")
        summary = summarize_text(transcript, config)

        summary_path = task_dir / "summary.txt"
        summary_path.write_text(summary, encoding="utf-8")
        print(f"[Step 4/4] Saved: summary.txt")
    else:
        print(f"\n[Step 4/4] Skipped (--no-summary)")

    # Cleanup
    if not keep_video and video_path.exists():
        video_path.unlink()
        print(f"[Cleanup] Removed video file")

    # Done
    elapsed = time.time() - start_time
    print(f"\n{'=' * 60}")
    print(f"Done! ({elapsed:.1f}s)")
    print(f"Output directory: {task_dir}")
    print(f"{'=' * 60}")

    return task_dir


def resume_pipeline(
    task_dir: str,
    config: dict,
    skip_summary: bool = False,
    keep_video: bool = True,
) -> Path:
    """Resume processing from an existing task directory.

    Detects which artifacts already exist and continues from the appropriate step:
    - Has video but no audio → extract audio, transcribe, summarize
    - Has audio but no transcript → transcribe, summarize
    - Has transcript but no summary → summarize

    Args:
        task_dir: Path to an existing task directory containing partial results.
        config: Full configuration dictionary.
        skip_summary: If True, only transcribe without summarizing.
        keep_video: If True, keep video file after processing.

    Returns:
        Path to the output directory.
    """
    start_time = time.time()
    task_dir = Path(task_dir)

    if not task_dir.is_dir():
        raise FileNotFoundError(f"Task directory not found: {task_dir}")

    print(f"{'=' * 60}")
    print(f"AI4VideoSummarize - Resume Mode")
    print(f"{'=' * 60}")
    print(f"Task directory: {task_dir}")

    # Detect existing artifacts
    video_path = _find_file(task_dir, [".mp4", ".mkv", ".webm", ".flv"])
    audio_path = _find_file(task_dir, [".mp3", ".wav"])
    transcript_path = _find_file(task_dir, [".txt"], prefix="transcript")
    srt_path = _find_file(task_dir, [".srt"], prefix="transcript")
    summary_path = _find_file(task_dir, [".txt"], prefix="summary")

    print(f"  Video:      {'✓ ' + video_path.name if video_path else '✗ not found'}")
    print(f"  Audio:      {'✓ ' + audio_path.name if audio_path else '✗ not found'}")
    print(f"  Transcript: {'✓ ' + transcript_path.name if transcript_path else '✗ not found'}")
    print(f"  SRT:        {'✓ ' + srt_path.name if srt_path else '✗ not found'}")
    print(f"  Summary:    {'✓ ' + summary_path.name if summary_path else '✗ not found'}")
    print(f"{'=' * 60}")

    # Determine where to resume
    if transcript_path and (summary_path or skip_summary):
        print("\nAll steps already completed. Nothing to do.")
        return task_dir

    # Step 2: Extract audio (if needed)
    if not audio_path:
        if not video_path:
            raise FileNotFoundError(
                f"No video or audio file found in {task_dir}. "
                "Cannot resume without at least a video or audio file."
            )
        print(f"\n[Step 2/4] Extracting audio...")
        audio_path = extract_audio(video_path, task_dir)
    else:
        print(f"\n[Step 2/4] Audio already exists, skipping.")

    # Step 3: Transcribe (if needed)
    if not transcript_path:
        print(f"\n[Step 3/4] Transcribing...")
        transcript, srt = transcribe_with_timestamps(audio_path, task_dir, config)

        transcript_path = task_dir / "transcript.txt"
        transcript_path.write_text(transcript, encoding="utf-8")
        print(f"[Step 3/4] Saved: transcript.txt")

        if srt:
            srt_path = task_dir / "transcript.srt"
            srt_path.write_text(srt, encoding="utf-8")
            print(f"[Step 3/4] Saved: transcript.srt")
    else:
        print(f"\n[Step 3/4] Transcript already exists, skipping.")

    # Step 4: Summarize (if needed)
    if not skip_summary and not summary_path:
        print(f"\n[Step 4/4] Summarizing...")
        transcript_text = transcript_path.read_text(encoding="utf-8")
        summary = summarize_text(transcript_text, config)

        summary_path = task_dir / "summary.txt"
        summary_path.write_text(summary, encoding="utf-8")
        print(f"[Step 4/4] Saved: summary.txt")
    elif skip_summary:
        print(f"\n[Step 4/4] Skipped (--no-summary)")
    else:
        print(f"\n[Step 4/4] Summary already exists, skipping.")

    # Cleanup
    if not keep_video and video_path and video_path.exists():
        video_path.unlink()
        print(f"[Cleanup] Removed video file")

    # Done
    elapsed = time.time() - start_time
    print(f"\n{'=' * 60}")
    print(f"Done! ({elapsed:.1f}s)")
    print(f"Output directory: {task_dir}")
    print(f"{'=' * 60}")

    return task_dir


def _find_file(directory: Path, extensions: list[str], prefix: str = None) -> Path | None:
    """Find a file in directory matching given extensions and optional prefix.

    Args:
        directory: Directory to search in.
        extensions: List of file extensions to match (e.g. ['.mp4', '.mkv']).
        prefix: If set, filename must start with this prefix.

    Returns:
        Path to the first matching file, or None.
    """
    for ext in extensions:
        if prefix:
            candidates = list(directory.glob(f"{prefix}{ext}"))
        else:
            candidates = [
                f for f in directory.glob(f"*{ext}")
                if not f.stem.startswith("audio_chunk_")
            ]
        if candidates:
            return candidates[0]
    return None
