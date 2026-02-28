"""Custom exceptions used across core."""


class OsdagError(Exception):
    """Base exception for all OsdagBridge errors."""

    pass


class DesignFailedError(OsdagError):
    """Raised when a design check fails (capacity < demand)."""

    pass


class InputValidationError(OsdagError):
    """Raised when input parameters are invalid."""

    pass


class SolverError(OsdagError):
    """Raised when a structural solver fails."""

    pass

