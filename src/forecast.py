"""
Candidate Forecasting Models and Estimator Pipelines for Project FORESIGHT.
Implements Ridge, HistGradientBoosting, and RandomForest estimators with non-negative constraints.
"""

from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.linear_model import Ridge
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

from src.config import config
from src.logging_utils import get_logger

logger = get_logger(__name__)

FEATURE_COLS_NUMERIC = [
    "unit_cost", "list_price", "lag_1", "lag_2", "lag_4", "lag_8", "lag_52",
    "roll_4_mean", "roll_4_std", "roll_8_mean", "roll_12_mean",
    "sin_week", "cos_week", "month", "is_holiday_week", "promo_active", "price_ratio"
]
FEATURE_COLS_CATEGORICAL = ["category", "subcategory"]


def create_preprocessor() -> ColumnTransformer:
    """Standard preprocessor encoding categoricals and scaling numerics."""
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), FEATURE_COLS_NUMERIC),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), FEATURE_COLS_CATEGORICAL)
        ],
        remainder="drop"
    )


class NonNegativeRegressor(BaseEstimator, RegressorMixin):
    """Wrapper that enforces non-negative demand predictions."""
    def __init__(self, base_estimator: Any = None):
        self.base_estimator = base_estimator

    def fit(self, X: Any, y: Any) -> "NonNegativeRegressor":
        from sklearn.base import clone
        self.base_estimator_ = clone(self.base_estimator)
        self.base_estimator_.fit(X, y)
        self.is_fitted_ = True
        return self

    def predict(self, X: Any) -> np.ndarray:
        check_estimator = getattr(self, "base_estimator_", self.base_estimator)
        preds = check_estimator.predict(X)
        return np.clip(preds, a_min=0.0, a_max=None)


def get_candidate_models() -> Dict[str, Pipeline]:
    """Returns dictionary of candidate forecasting pipelines."""
    models = {
        "Ridge_Linear": Pipeline([
            ("preprocessor", create_preprocessor()),
            ("regressor", NonNegativeRegressor(Ridge(alpha=10.0, random_state=config.RANDOM_SEED)))
        ]),
        "HistGradientBoosting": Pipeline([
            ("preprocessor", create_preprocessor()),
            ("regressor", NonNegativeRegressor(
                HistGradientBoostingRegressor(
                    max_iter=100,
                    learning_rate=0.08,
                    max_depth=5,
                    random_state=config.RANDOM_SEED
                )
            ))
        ]),
        "RandomForest": Pipeline([
            ("preprocessor", create_preprocessor()),
            ("regressor", NonNegativeRegressor(
                RandomForestRegressor(
                    n_estimators=80,
                    max_depth=8,
                    random_state=config.RANDOM_SEED,
                    n_jobs=-1
                )
            ))
        ])
    }
    return models
