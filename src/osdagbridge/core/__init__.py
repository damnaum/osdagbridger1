"""Core package for OsdagBridge - analysis and design of steel bridges."""
from .exceptions import (
    OsdagError,
    DesignFailedError,
    InputValidationError,
    SolverError,
)

__all__ = [
    "OsdagError",
    "DesignFailedError",
    "InputValidationError",
    "SolverError",
]

