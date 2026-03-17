# core/constants.py
"""Central numeric constants for the v5 DRL-VSL stack."""

MAX_SPEED_KPH: float = 130.0
"""Default maximum speed limit (km/h) for VSL components."""

DEFAULT_MIN_SPEED_KPH: float = 50.0
"""Recommended lower bound when clamping VSL actions."""

DEFAULT_VSL_SPEED_STEP_KPH: float = 5.0
"""Granularity for multi-segment VSL adjustments."""

MAX_ADJACENT_DIFF_KPH: float = 10.0
"""Maximum allowed differential between adjacent signs (MUTCD guideline)."""

DEFAULT_MAX_ACTION_DELTA_KPH: float = 20.0
"""Upper bound for per-step VSL magnitude changes."""
