"""Configuration loading utilities."""

from pathlib import Path
from typing import Any

import yaml


def load_config(path: str | Path = "config/default.yaml") -> dict[str, Any]:
    """Load a YAML configuration file."""

    with Path(path).open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    return config or {}
