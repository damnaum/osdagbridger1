"""Core package for OsdagBridge — analysis and design of steel bridges.

Public API surface re-exported for convenience.
"""

from .exceptions import (
    CodeNotFoundError,
    ConfigurationError,
    DesignFailedError,
    InputValidationError,
    OsdagError,
    SolverError,
)

__all__ = [
    "CodeNotFoundError",
    "ConfigurationError",
    "DesignFailedError",
    "InputValidationError",
    "OsdagError",
    "SolverError",
]

