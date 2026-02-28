"""Custom exceptions for the OsdagBridge core.

Every public exception descends from ``OsdagError``, so callers can
catch the whole lot with a single ``except OsdagError``.
"""

from __future__ import annotations


class OsdagError(Exception):
    """Root exception for anything OsdagBridge raises."""


class DesignFailedError(OsdagError):
    """A design check came up short (demand > capacity)."""

    def __init__(self, check_name: str, demand: float, capacity: float) -> None:
        self.check_name = check_name
        self.demand = demand
        self.capacity = capacity
        super().__init__(
            f"{check_name}: demand {demand:.2f} exceeds capacity {capacity:.2f}"
        )


class InputValidationError(OsdagError):
    """Input parameters are out of range or nonsensical."""


class SolverError(OsdagError):
    """The structural solver blew up or didn't converge."""


class ConfigurationError(OsdagError):
    """YAML / config file is malformed or missing required keys."""


class CodeNotFoundError(OsdagError):
    """No design-code module registered under the requested name."""

    def __init__(self, code_name: str) -> None:
        self.code_name = code_name
        super().__init__(f"Design code '{code_name}' is not registered.")

