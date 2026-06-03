"""Configuration management module."""

import os
import yaml
from pathlib import Path

DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"


def load_config(config_path: str = None) -> dict:
    """Load configuration from YAML file.

    Args:
        config_path: Path to config file. If None, uses default location.

    Returns:
        Configuration dictionary.

    Raises:
        FileNotFoundError: If config file does not exist.
    """
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH

    if not path.exists():
        raise FileNotFoundError(
            f"Config file not found: {path}\n"
            f"Please copy config.yaml.example to config.yaml and fill in your API keys."
        )

    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Allow environment variable overrides
    if os.environ.get("WHISPER_API_KEY"):
        config.setdefault("whisper", {})["api_key"] = os.environ["WHISPER_API_KEY"]
    if os.environ.get("WHISPER_BASE_URL"):
        config.setdefault("whisper", {})["base_url"] = os.environ["WHISPER_BASE_URL"]
    if os.environ.get("LLM_API_KEY"):
        config.setdefault("llm", {})["api_key"] = os.environ["LLM_API_KEY"]
    if os.environ.get("LLM_BASE_URL"):
        config.setdefault("llm", {})["base_url"] = os.environ["LLM_BASE_URL"]

    return config
