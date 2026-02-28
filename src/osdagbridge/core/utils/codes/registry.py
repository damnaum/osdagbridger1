"""Registry for looking up Indian design code modules by name."""
from typing import Any, Dict

_CODE_REGISTRY: Dict[str, Any] = {}


def register_code(name: str, module: Any) -> None:
    """Register a code module (e.g., 'IRC:6-2017')."""
    _CODE_REGISTRY[name] = module


def get_code(name: str) -> Any:
    """Retrieve a registered code module by name. Returns None if not found."""
    return _CODE_REGISTRY.get(name)


def list_codes() -> list:
    """List all registered code names."""
    return list(_CODE_REGISTRY.keys())


# Auto-register available codes on import
def _auto_register():
    from . import irc6_2017, load_combinations
    register_code("IRC:6-2017", irc6_2017)
    register_code("load_combinations", load_combinations)


_auto_register()

