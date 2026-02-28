"""Quick-and-dirty input guards for engineering parameters."""


def validate_positive(value: float, name: str) -> float:
    """Ensure a value is strictly positive, raise ValueError if not."""
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")
    return value


def validate_range(
    value: float, min_val: float, max_val: float, name: str
) -> float:
    """Ensure a value is within [min_val, max_val]."""
    if not (min_val <= value <= max_val):
        raise ValueError(
            f"{name} must be between {min_val} and {max_val}, got {value}"
        )
    return value


def validate_span_depth_ratio(
    span: float,
    depth: float,
    min_ratio: float = 10,
    max_ratio: float = 25,
) -> None:
    """Validate span-to-depth ratio is within engineering limits."""
    ratio = span / depth if depth > 0 else float("inf")
    if not (min_ratio <= ratio <= max_ratio):
        raise ValueError(
            f"Span/depth ratio {ratio:.1f} outside recommended range "
            f"[{min_ratio}, {max_ratio}]"
        )


def validate_slenderness(value: float, limit: float, element: str) -> bool:
    """Check if slenderness ratio is within limit. Returns True if OK."""
    return value <= limit

