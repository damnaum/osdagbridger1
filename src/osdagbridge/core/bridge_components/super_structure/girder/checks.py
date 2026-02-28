"""Local flange and web buckling checks for I-girders.

Reference: IS 800:2007 Table 2, Clause 8.6.
"""

from __future__ import annotations

import math


def check_flange_outstand(
    b_f: float, t_w: float, t_f: float, fy: float
) -> dict:
    """Check compression flange outstand as per IS 800 Table 2.

    Args:
        b_f: Flange width (mm).
        t_w: Web thickness (mm).
        t_f: Flange thickness (mm).
        fy: Yield strength (MPa).

    Returns:
        dict with outstand ratio, limit, and pass/fail.
    """
    epsilon = math.sqrt(250.0 / fy)
    outstand = (b_f - t_w) / (2 * t_f)
    limit_compact = 9.4 * epsilon
    return {
        "outstand_ratio": round(outstand, 2),
        "compact_limit": round(limit_compact, 2),
        "ok": outstand <= limit_compact,
    }


def check_web_slenderness(
    d_w: float, t_w: float, fy: float
) -> dict:
    """Check web slenderness as per IS 800 Table 2.

    Args:
        d_w: Web depth (mm).
        t_w: Web thickness (mm).
        fy: Yield strength (MPa).

    Returns:
        dict with slenderness, limit, and pass/fail.
    """
    epsilon = math.sqrt(250.0 / fy)
    slenderness = d_w / t_w
    limit_compact = 105 * epsilon
    return {
        "web_slenderness": round(slenderness, 2),
        "compact_limit": round(limit_compact, 2),
        "ok": slenderness <= limit_compact,
    }
