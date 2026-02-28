"""Local flange & web buckling checks (IS 800:2007 Table 2)."""

from __future__ import annotations

import math


def check_flange_outstand(
    b_f: float, t_w: float, t_f: float, fy: float
) -> dict:
    """Compression-flange outstand ratio vs compact limit."""
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
    """Web d/t slenderness check against the compact limit."""
    epsilon = math.sqrt(250.0 / fy)
    slenderness = d_w / t_w
    limit_compact = 105 * epsilon
    return {
        "web_slenderness": round(slenderness, 2),
        "compact_limit": round(limit_compact, 2),
        "ok": slenderness <= limit_compact,
    }
