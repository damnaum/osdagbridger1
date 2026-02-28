"""Bridge-type registry.

Each bridge type lives in its own sub-package (plate_girder, box_girder,
truss …) and exposes a common interface: dto, initial_sizing, analyser,
designer, cad_generator, report_generator.
"""

from __future__ import annotations

from typing import Any, Dict

_BRIDGE_TYPE_REGISTRY: Dict[str, Any] = {}


def register_bridge_type(name: str, module: Any) -> None:
    """Register a bridge-type module (e.g., 'plate_girder')."""
    _BRIDGE_TYPE_REGISTRY[name] = module


def get_bridge_type(name: str) -> Any:
    """Retrieve a bridge-type module by name.  Returns *None* if not found."""
    return _BRIDGE_TYPE_REGISTRY.get(name)


def list_bridge_types() -> list[str]:
    """List all registered bridge-type names."""
    return list(_BRIDGE_TYPE_REGISTRY.keys())


# Auto-register available bridge types on import
def _auto_register() -> None:
    from . import plate_girder

    register_bridge_type("plate_girder", plate_girder)

    # Stubs — registered but marked as not-yet-implemented
    from . import box_girder, truss

    register_bridge_type("box_girder", box_girder)
    register_bridge_type("truss", truss)


_auto_register()
