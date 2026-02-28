"""ospgrillage adapter (optional dependency).

Wraps the ospgrillage library for full grillage analysis.
Install with ``pip install ospgrillage`` if needed.
"""


class OspGrillageAdapter:
    """Thin wrapper around the ospgrillage grillage modeller."""

    def __init__(self):
        self._available = False
        try:
            import ospgrillage as osp

            self._osp = osp
            self._available = True
        except ImportError:
            self._osp = None

    @property
    def is_available(self) -> bool:
        """Check if ospgrillage is installed."""
        return self._available

    def analyze_grillage(
        self,
        span: float,
        width: float,
        num_girders: int,
        girder_spacing: float,
        loads: list,
    ) -> dict:
        """Run a grillage analysis for bridge deck.

        Args:
            span: Bridge span in mm
            width: Bridge deck width in mm
            num_girders: Number of main girders
            girder_spacing: Centre-to-centre girder spacing in mm
            loads: List of load dictionaries

        Returns:
            Dictionary with analysis results

        Raises:
            RuntimeError: If ospgrillage is not installed
        """
        if not self._available:
            raise RuntimeError(
                "ospgrillage is not installed. "
                "Install with: pip install ospgrillage"
            )
        # Placeholder for full grillage model building
        return {
            "girder_moments": [],
            "girder_shears": [],
            "max_deflection": 0.0,
            "status": "not_implemented_yet",
        }

