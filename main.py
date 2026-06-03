#!/usr/bin/env python3
"""AI4VideoSummarize - Video transcription and summarization tool."""

import argparse
import sys
from pathlib import Path

from src.config import load_config
from src.pipeline import run_pipeline, resume_pipeline


def main():
    parser = argparse.ArgumentParser(
        description="AI4VideoSummarize: Transcribe and summarize videos using LLM APIs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /path/to/video.mp4
  %(prog)s "https://www.youtube.com/watch?v=xxxxx"
  %(prog)s "https://www.bilibili.com/video/BVxxxxx"
  %(prog)s --no-summary "https://www.youtube.com/watch?v=xxxxx"
  %(prog)s --config my_config.yaml --output ./results "https://..."
  %(prog)s --resume ./output/20240101_120000_video_title
        """,
    )

    parser.add_argument(
        "source",
        nargs="?",
        default=None,
        help="Video source: local file path, YouTube URL, Bilibili URL, or direct video URL",
    )
    parser.add_argument(
        "--resume",
        "-r",
        default=None,
        metavar="DIR",
        help="Resume processing from an existing task directory",
    )
    parser.add_argument(
        "--config",
        "-c",
        default="./config.yaml",
        help="Path to config file (default: ./config.yaml)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Output base directory (default: from config or ./output)",
    )
    parser.add_argument(
        "--no-summary",
        action="store_true",
        help="Only transcribe, skip summarization",
    )
    parser.add_argument(
        "--no-keep-video",
        action="store_true",
        help="Delete downloaded video after processing",
    )

    args = parser.parse_args()

    # Validate: must provide either source or --resume
    if not args.source and not args.resume:
        parser.error("Please provide a video source or use --resume to resume from a directory.")
    if args.source and args.resume:
        parser.error("Cannot use both a video source and --resume at the same time.")

    try:
        # Load config
        config = load_config(args.config)

        if args.resume:
            # Resume mode
            output_dir = resume_pipeline(
                task_dir=args.resume,
                config=config,
                skip_summary=args.no_summary,
                keep_video=not args.no_keep_video,
            )
        else:
            # Normal mode
            output_dir = run_pipeline(
                source=args.source,
                config=config,
                output_base=args.output,
                skip_summary=args.no_summary,
                keep_video=not args.no_keep_video,
            )

        print(f"\nResults saved to: {output_dir}")

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
