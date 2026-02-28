"""Custom exceptions used across the OsdagBridge core.

All public exceptions inherit from :class:`OsdagError` so that callers
can catch the whole family with a single ``except OsdagError`` clause.
"""

from __future__ import annotations


class OsdagError(Exception):
    """Base exception for all OsdagBridge errors."""


class DesignFailedError(OsdagError):
    """Raised when a design check fails (capacity < demand)."""

    def __init__(self, check_name: str, demand: float, capacity: float) -> None:
        self.check_name = check_name
        self.demand = demand
        self.capacity = capacity
        super().__init__(
            f"{check_name}: demand {demand:.2f} exceeds capacity {capacity:.2f}"
        )


class InputValidationError(OsdagError):
    """Raised when input parameters are invalid or out of range."""


class SolverError(OsdagError):
    """Raised when a structural solver fails to converge or errors out."""


class ConfigurationError(OsdagError):
    """Raised when a configuration file is malformed or missing keys."""


class CodeNotFoundError(OsdagError):
    """Raised when a requested design code module is not registered."""

    def __init__(self, code_name: str) -> None:
        self.code_name = code_name
        super().__init__(f"Design code '{code_name}' is not registered.")

