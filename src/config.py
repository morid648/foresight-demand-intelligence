"""
Centralized Configuration Module for Project FORESIGHT.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class ProjectConfig(BaseSettings):
    """Configuration settings loaded from environment or defaults."""
    model_config = SettingsConfigDict(
        env_file=".env" if os.path.exists(".env") else None,
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Project Metadata
    PROJECT_NAME: str = "FORESIGHT"
    CLIENT_NAME: str = "NorthBay Living"
    ENVIRONMENT: str = "production"
    RANDOM_SEED: int = 42

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_RAW_DIR: Path = BASE_DIR / "data" / "raw"
    DATA_SAMPLE_DIR: Path = BASE_DIR / "data" / "sample"
    DATA_PROCESSED_DIR: Path = BASE_DIR / "data" / "processed"
    ARTIFACTS_DIR: Path = BASE_DIR / "artifacts"
    REPORTS_DIR: Path = BASE_DIR / "reports"
    DOCS_DIR: Path = BASE_DIR / "docs"

    # Forecasting Parameters
    FORECAST_HORIZON_WEEKS: int = 8
    SEASONAL_PERIOD_WEEKS: int = 52
    MIN_HISTORY_FOR_SEASONAL_NAIVE: int = 52
    BACKTEST_FOLDS: int = 4
    BACKTEST_STEP_WEEKS: int = 4

    # Inventory Risk Parameters
    SAFETY_STOCK_Z: float = 1.65  # 95% cycle service level
    OVERSTOCK_HORIZON_WEEKS: int = 12  # Window to evaluate forward overstock accumulation
    HIGH_STOCKOUT_RISK_THRESHOLD: float = 0.50
    HIGH_OVERSTOCK_RISK_THRESHOLD: float = 0.50

    # Logging
    LOG_LEVEL: str = "INFO"


# Global singleton configuration instance
config = ProjectConfig()
