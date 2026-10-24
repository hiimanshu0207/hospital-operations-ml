"""
Feature engineering and preprocessing pipeline for hospital operational ML models.

Adheres strictly to the following principles:
1. Strict Featurization Ordering: Encoders and scalers fit ONLY on training sets.
2. Target Leakage Prevention: Excludes future service milestones and downstream outcomes
   (service start/end, waiting time, LOS, final status).
3. Deterministic Preprocessing: Identical inputs produce identical feature vectors.
"""

from typing import Any
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# Post-arrival outcomes that MUST NEVER be used as prediction inputs
PROHIBITED_LEAKAGE_COLUMNS = {
    "service_start_timestamp",
    "service_end_timestamp",
    "waiting_time_minutes",
    "length_of_stay_minutes",
    "total_duration_minutes",
    "status",
    "bed_id",
}

# Ordinal mapping for non-identifying age groups
AGE_GROUP_MAP = {
    "0-17": 0,
    "18-35": 1,
    "36-50": 2,
    "51-65": 3,
    "65+": 4,
}

DEPT_CODES = ["ED", "ICU", "GEN", "SURG", "PED"]


def extract_prediction_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract raw feature set available strictly at patient arrival/triage.

    Guarantees no target leakage by discarding all downstream service milestone columns.
    """
    data = df.copy()

    # 1. Parse arrival timestamp
    arrival = pd.to_datetime(data["arrival_timestamp"])
    data["arrival_hour"] = arrival.dt.hour
    data["arrival_day_of_week"] = arrival.dt.day_of_week
    data["is_weekend"] = (data["arrival_day_of_week"] >= 5).astype(int)
    data["is_night_shift"] = (data["arrival_hour"].isin([22, 23, 0, 1, 2, 3, 4, 5, 6])).astype(int)
    data["is_peak_hours"] = (data["arrival_hour"].between(10, 19)).astype(int)

    # 2. Cyclical temporal transforms (captures 24h and 7d continuity)
    data["sin_hour"] = np.sin(2 * np.pi * data["arrival_hour"] / 24.0)
    data["cos_hour"] = np.cos(2 * np.pi * data["arrival_hour"] / 24.0)
    data["sin_day"] = np.sin(2 * np.pi * data["arrival_day_of_week"] / 7.0)
    data["cos_day"] = np.cos(2 * np.pi * data["arrival_day_of_week"] / 7.0)

    # 3. Operational queue dynamics
    data["queue_length"] = data["queue_length_at_arrival"].clip(lower=0)
    data["staff_available"] = data["staff_available_at_arrival"].clip(lower=1)
    data["queue_to_staff_ratio"] = data["queue_length"] / data["staff_available"]
    data["high_queue_flag"] = (data["queue_length"] >= 5).astype(int)

    # 4. Triage acuity & demographics
    data["acuity_level"] = data["acuity_level"].astype(int)
    data["is_critical_acuity"] = (data["acuity_level"] <= 2).astype(int)
    data["age_group_code"] = data["patient_age_group"].map(AGE_GROUP_MAP).fillna(1).astype(int)

    # 5. Department identification
    if "dept_code" not in data.columns and "department_id" in data.columns:
        dept_id_to_code = {1: "ED", 2: "ICU", 3: "GEN", 4: "SURG", 5: "PED"}
        data["dept_code"] = data["department_id"].map(dept_id_to_code).fillna("ED")

    return data


class HospitalFeaturePipeline(BaseEstimator, TransformerMixin):
    """
    Production-ready feature preprocessing pipeline with strict leakage protection.

    Fits OneHotEncoder and StandardScaler on training data only.
    """

    def __init__(self, scale_numeric: bool = True):
        self.scale_numeric = scale_numeric
        self.dept_encoder = OneHotEncoder(categories=[DEPT_CODES], sparse_output=False, handle_unknown="ignore")
        self.scaler = StandardScaler()
        self.fitted_ = False
        self.feature_names_: list[str] = []

    def fit(self, X: pd.DataFrame, y: Any = None):
        """Fit preprocessing transformations strictly on input features."""
        # Leakage check: inspect for prohibited columns in feature matrix
        leaked_cols = set(X.columns).intersection(PROHIBITED_LEAKAGE_COLUMNS)
        if leaked_cols:
            raise ValueError(f"Target Leakage Detected! Features contain prohibited columns: {leaked_cols}")

        processed = extract_prediction_time_features(X)

        # Fit department one-hot encoder
        dept_cats = processed[["dept_code"]]
        self.dept_encoder.fit(dept_cats)

        # Numeric features to scale
        numeric_cols = [
            "queue_length",
            "staff_available",
            "queue_to_staff_ratio",
            "acuity_level",
            "age_group_code",
            "sin_hour",
            "cos_hour",
            "sin_day",
            "cos_day",
        ]
        if self.scale_numeric:
            self.scaler.fit(processed[numeric_cols])

        # Feature names tracking
        dept_names = [f"dept_{c}" for c in self.dept_encoder.categories_[0]]
        binary_names = ["is_weekend", "is_night_shift", "is_peak_hours", "high_queue_flag", "is_critical_acuity"]
        self.feature_names_ = numeric_cols + binary_names + dept_names
        self.fitted_ = True
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Transform features using fitted encoders and scalers."""
        if not self.fitted_:
            raise RuntimeError("Pipeline must be fitted before calling transform.")

        # Leakage check
        leaked_cols = set(X.columns).intersection(PROHIBITED_LEAKAGE_COLUMNS)
        if leaked_cols:
            raise ValueError(f"Target Leakage Detected! Features contain prohibited columns: {leaked_cols}")

        processed = extract_prediction_time_features(X)

        numeric_cols = [
            "queue_length",
            "staff_available",
            "queue_to_staff_ratio",
            "acuity_level",
            "age_group_code",
            "sin_hour",
            "cos_hour",
            "sin_day",
            "cos_day",
        ]

        if self.scale_numeric:
            scaled_num = self.scaler.transform(processed[numeric_cols])
        else:
            scaled_num = processed[numeric_cols].values

        encoded_dept = self.dept_encoder.transform(processed[["dept_code"]])

        binary_cols = ["is_weekend", "is_night_shift", "is_peak_hours", "high_queue_flag", "is_critical_acuity"]
        binary_vals = processed[binary_cols].values

        combined_matrix = np.hstack([scaled_num, binary_vals, encoded_dept])
        return pd.DataFrame(combined_matrix, columns=self.feature_names_, index=X.index)

    def fit_transform(self, X: pd.DataFrame, y: Any = None) -> pd.DataFrame:
        """Fit and transform in a single call."""
        return self.fit(X, y).transform(X)


# ---------------------------------------------------------------------------
# Target Extraction Helpers (Explicit Separation)
# ---------------------------------------------------------------------------

def get_waiting_time_target(df: pd.DataFrame) -> pd.Series:
    """Extract continuous waiting time target for regression models (Day 5)."""
    if "waiting_time_minutes" not in df.columns:
        raise KeyError("Column 'waiting_time_minutes' not found in DataFrame.")
    return df["waiting_time_minutes"].astype(float)


def get_hourly_demand_series(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate encounters into an hourly time-series for demand forecasting (Day 4).

    Returns:
        DataFrame with DatetimeIndex and arrival count.
    """
    arrival_dt = pd.to_datetime(df["arrival_timestamp"])
    # Resample by hour
    hourly = arrival_dt.dt.floor("1h").value_counts().sort_index()

    # Fill full date range with 0 if gaps exist
    full_idx = pd.date_range(start=hourly.index.min(), end=hourly.index.max(), freq="1h")
    hourly_df = hourly.reindex(full_idx, fill_value=0).to_frame(name="arrival_count")
    hourly_df.index.name = "timestamp"
    return hourly_df


def prepare_waiting_time_dataset(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """
    Split raw dataset into leakage-free prediction feature set (X) and target (y).
    """
    y = get_waiting_time_target(df)

    # Strictly drop all prohibited leakage columns from raw input
    safe_cols = [c for c in df.columns if c not in PROHIBITED_LEAKAGE_COLUMNS]
    X_raw = df[safe_cols].copy()

    return X_raw, y
