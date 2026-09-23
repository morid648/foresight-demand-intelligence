"""
I/O and Data Persistence Utilities for Project FORESIGHT.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union
import pandas as pd
from src.logging_utils import get_logger

logger = get_logger(__name__)


def ensure_dir(directory_path: Union[str, Path]) -> Path:
    """Ensures a directory exists, creating parents if necessary."""
    path = Path(directory_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_dataframe(
    df: pd.DataFrame,
    file_path: Union[str, Path],
    format: str = "parquet",
    **kwargs: Any
) -> Path:
    """Saves a pandas DataFrame atomically to parquet or csv."""
    path = Path(file_path)
    ensure_dir(path.parent)

    if format == "parquet" or path.suffix == ".parquet":
        df.to_parquet(path, index=False, **kwargs)
    elif format == "csv" or path.suffix == ".csv":
        df.to_csv(path, index=False, **kwargs)
    else:
        raise ValueError(f"Unsupported DataFrame format: {format} ({path.suffix})")

    logger.info(f"Saved DataFrame ({len(df)} rows, {len(df.columns)} cols) to {path}")
    return path


def load_dataframe(file_path: Union[str, Path], **kwargs: Any) -> pd.DataFrame:
    """Loads a DataFrame from parquet or csv."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Requested dataset file not found: {path}")

    if path.suffix == ".parquet":
        df = pd.read_parquet(path, **kwargs)
    elif path.suffix == ".csv":
        df = pd.read_csv(path, **kwargs)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")

    logger.info(f"Loaded DataFrame ({len(df)} rows) from {path}")
    return df


def save_json(data: Union[Dict[str, Any], list], file_path: Union[str, Path], indent: int = 2) -> Path:
    """Saves dictionary/list structure to a formatted JSON file."""
    path = Path(file_path)
    ensure_dir(path.parent)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, default=str)

    logger.info(f"Saved JSON artifact to {path}")
    return path


def load_json(file_path: Union[str, Path]) -> Union[Dict[str, Any], list]:
    """Loads a JSON file into a Python object."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Requested JSON file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
