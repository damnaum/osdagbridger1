"""
IRC:22-2015 — Standard Specifications for Road Bridges
Section VI: Composite Construction (Steel-Concrete)

Provides modular ratio, effective width, and composite section capacity.
Reference: IRC:22-2015
"""


def get_modular_ratio(fck: float) -> float:
    """Get modular ratio (Es/Ec) for composite design.

    Args:
        fck: Characteristic compressive strength of concrete in MPa

    Returns:
        Modular ratio m = Es / Ec

    Reference: IRC:22-2015, Clause 604.3
    """
    ec = 5000 * (fck ** 0.5)  # Short-term Ec in MPa (IS 456)
    es = 200_000.0  # MPa
    return es / ec


def get_effective_flange_width(
    span: float, spacing: float, slab_thickness: float
) -> float:
    """Effective flange width of concrete slab for composite action.

    Args:
        span: Effective span in mm
        spacing: Centre-to-centre spacing of girders in mm
        slab_thickness: Thickness of concrete deck slab in mm

    Returns:
        Effective flange width in mm

    Reference: IRC:22-2015, Clause 603.2
    """
    beff_options = [
        span / 4,
        spacing,
        12 * slab_thickness + spacing / 2,  # Approximate for interior girder
    ]
    return min(beff_options)


def get_creep_modular_ratio(
    fck: float, creep_coefficient: float = 1.5
) -> float:
    """Long-term modular ratio considering creep.

    Args:
        fck: Concrete grade in MPa
        creep_coefficient: Creep coefficient (default 1.5 for normal conditions)

    Returns:
        Long-term modular ratio

    Reference: IRC:22-2015, Clause 604.3
    """
    short_term = get_modular_ratio(fck)
    return short_term * (1 + creep_coefficient)

