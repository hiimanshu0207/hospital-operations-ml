"""
Machine Learning & Analytics package for Hospital Operations & Workflow Optimization.
"""

from ml.features import (
    HospitalFeaturePipeline,
    extract_prediction_time_features,
    prepare_waiting_time_dataset,
    get_waiting_time_target,
    get_hourly_demand_series,
    PROHIBITED_LEAKAGE_COLUMNS,
)
from ml.audit_dataset import run_dataset_audit
from ml.eda import run_eda
from ml.demand_forecast import (
    build_continuous_hourly_demand_series,
    create_demand_features,
    chronological_split,
    train_and_evaluate_demand_models,
    predict_future_demand,
)

__all__ = [
    "HospitalFeaturePipeline",
    "extract_prediction_time_features",
    "prepare_waiting_time_dataset",
    "get_waiting_time_target",
    "get_hourly_demand_series",
    "PROHIBITED_LEAKAGE_COLUMNS",
    "run_dataset_audit",
    "run_eda",
    "build_continuous_hourly_demand_series",
    "create_demand_features",
    "chronological_split",
    "train_and_evaluate_demand_models",
    "predict_future_demand",
]
