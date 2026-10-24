"""
Pydantic schemas for hospital resource utilization, what-if simulation, and staff allocation optimization.
"""

from typing import Any
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Utilization Schemas
# ---------------------------------------------------------------------------

class BedCapacityInfo(BaseModel):
    total_beds: int
    occupied_beds: int
    available_beds: int
    utilization_rate_pct: float
    status: str
    data_source: str = "OBSERVED_DATABASE_STATE"


class StaffingInfo(BaseModel):
    active_staff_total: int
    staff_by_shift: dict[str, int]
    staff_by_role: dict[str, int]
    nurse_count: int
    target_nurse_to_patient_ratio: float
    required_nurses_for_census: int
    ratio_compliant: bool
    data_source: str = "OBSERVED_DATABASE_STATE"


class QueueAndDemandInfo(BaseModel):
    current_queue_estimate: int
    queue_to_staff_ratio: float
    queue_pressure_level: str
    data_source: str = "OBSERVED_DATABASE_STATE"


class EstimatedWaitTimeInfo(BaseModel):
    benchmark_acuity_level: int = 3
    estimated_minutes: float
    data_source: str = "ML_MODEL_ESTIMATE"


class DepartmentUtilization(BaseModel):
    department_code: str
    department_name: str
    bed_capacity: BedCapacityInfo
    staffing: StaffingInfo
    queue_and_demand: QueueAndDemandInfo
    estimated_wait_time: EstimatedWaitTimeInfo
    warnings: list[str]


class HospitalSummary(BaseModel):
    total_beds: int
    total_occupied_beds: int
    total_available_beds: int
    overall_bed_utilization_pct: float
    total_active_staff: int
    active_warning_count: int
    operational_stress_index: float


class ResourceUtilizationResponse(BaseModel):
    analysis_generated_at: str
    hospital_summary: HospitalSummary
    department_utilization: list[DepartmentUtilization]
    active_warnings: list[str]
    disclaimer: str


# ---------------------------------------------------------------------------
# What-If Simulation Schemas
# ---------------------------------------------------------------------------

class WhatIfSimulationRequest(BaseModel):
    """Parameters for simulating operational shifts and surges."""
    arrival_surge_pct: float = Field(
        default=0.0,
        ge=-50.0,
        le=100.0,
        description="Percentage surge or drop in patient arrivals (-50% to +100%)",
        examples=[20.0],
    )
    staff_adjustments: dict[str, int] = Field(
        default_factory=dict,
        description="Department staff additions or reductions (e.g., {'ED': 2, 'GEN': -1})",
        examples=[{"ED": 2, "GEN": -1}],
    )
    bed_capacity_adjustments: dict[str, int] = Field(
        default_factory=dict,
        description="Department bed capacity additions or reductions (e.g., {'ED': 5})",
        examples=[{"ED": 5}],
    )
    time_horizon_hours: int = Field(
        default=12,
        ge=1,
        le=72,
        description="Simulation horizon in hours (1 to 72)",
        examples=[12],
    )
    simulation_seed: int = Field(
        default=42,
        description="Random seed for reproducible stochastic simulations",
        examples=[42],
    )


class DepartmentSimulationState(BaseModel):
    total_beds: int
    occupied_beds: int
    bed_utilization_pct: float
    active_staff: int
    queue_length: int
    estimated_wait_time_minutes: float


class DepartmentSimulationDelta(BaseModel):
    staff_change: int
    bed_capacity_change: int
    queue_length_delta: int
    wait_time_delta_minutes: float
    bed_utilization_delta_pct: float


class DepartmentSimulationComparison(BaseModel):
    department_code: str
    department_name: str
    baseline: DepartmentSimulationState
    simulated: DepartmentSimulationState
    delta: DepartmentSimulationDelta
    projected_warnings: list[str]


class SimulationOverallImpact(BaseModel):
    average_baseline_wait_minutes: float
    average_simulated_wait_minutes: float
    net_wait_time_delta_minutes: float
    surge_severity: str


class WhatIfSimulationResponse(BaseModel):
    simulation_parameters: dict[str, Any]
    overall_impact: SimulationOverallImpact
    department_comparisons: list[DepartmentSimulationComparison]
    assumptions: list[str]
    disclaimer: str


# ---------------------------------------------------------------------------
# Staff Allocation Optimizer Schemas
# ---------------------------------------------------------------------------

class StaffAllocationRequest(BaseModel):
    """Parameters for constraint-aware staff allocation optimization."""
    shift: str = Field(
        default="All",
        description="Target shift to optimize ('Morning', 'Evening', 'Night', or 'All')",
        examples=["All"],
    )
    total_staff_budget: int | None = Field(
        default=None,
        ge=5,
        le=300,
        description="Total staff budget to conserve. Defaults to current active staff count.",
        examples=[84],
    )
    min_staff_per_dept: dict[str, int] | None = Field(
        default=None,
        description="Mandatory minimum staffing per department code to ensure patient safety",
        examples=[{"ED": 4, "ICU": 3}],
    )
    max_staff_per_dept: dict[str, int] | None = Field(
        default=None,
        description="Maximum physical/supervisory capacity per department code",
        examples=[{"ED": 20, "ICU": 10}],
    )
    priority_weights: dict[str, float] | None = Field(
        default=None,
        description="Clinical acuity weighting factors by department code",
        examples=[{"ICU": 2.5, "ED": 2.0}],
    )


class DepartmentStaffRecommendation(BaseModel):
    department_code: str
    department_name: str
    current_staff: int
    recommended_staff: int
    net_change: int
    minimum_staff_constraint: int
    maximum_staff_constraint: int
    rule_based_baseline_staff: int
    rationale: str


class StaffAllocationResponse(BaseModel):
    shift: str
    total_staff_budget: int
    total_current_staff: int
    total_allocated_staff: int
    budget_conserved: bool
    optimizer_status: str
    objective_score: float
    recommendations: list[DepartmentStaffRecommendation]
    rule_based_comparison: dict[str, Any]
    governance_notice: str
