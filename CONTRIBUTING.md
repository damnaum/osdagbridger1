# Contributing to OsdagBridge

Thank you for your interest in contributing to OsdagBridge! This document provides guidelines and instructions for contributing.

## Getting Started

### 1. Fork and Clone

```bash
git clone https://github.com/<your-username>/bridge.git
cd bridge
```

### 2. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 3. Install in Editable Mode

```bash
pip install -e ".[dev]"
```

This installs the package with all development dependencies (pytest, ruff, mypy).

### 4. Make Your Changes

- Write clean, well-documented code with type hints
- Follow existing code patterns and conventions
- Keep line length ≤ 100 characters (enforced by ruff)

### 5. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=osdagbridge --cov-report=term-missing

# Run a specific test file
pytest tests/unit/test_designer.py -v
```

All tests must pass before submitting a PR.

### 6. Run Linting

```bash
ruff check src/ tests/
```

Fix any issues reported by ruff before submitting.

### 7. Submit a Pull Request

- Push your branch to your fork
- Open a PR against the `main` branch
- Provide a clear description of your changes
- Reference any related issues

## Code Standards

### Engineering Formula References

**All structural engineering formulas must reference the exact clause number** from the relevant Indian Standard. For example:

```python
def calculate_shear_capacity(d, tw, fy):
    """Plastic shear capacity per IS 800:2007 Clause 8.4.1."""
    Av = d * tw
    Vd = Av * fy / (math.sqrt(3) * gamma_m0)  # IS 800 Cl 8.4.1
    return Vd
```

### Applicable Codes

- **IS 800:2007** — General Construction in Steel (Limit State Method)
- **IRC:6-2017** — Standard Specifications for Road Bridges, Section II: Loads and Load Combinations
- **IRC:22-2015** — Standard Specifications for Road Bridges, Section VI: Composite Construction
- **IRC:24-2010** — Standard Specifications for Road Bridges, Section V: Steel Road Bridges

### Units Convention

All internal calculations use a consistent unit system:

| Quantity    | Unit  |
|-------------|-------|
| Length      | mm    |
| Force       | kN    |
| Stress      | MPa   |
| Moment      | kN·m  |

Conversion helpers are available in `osdagbridge.core.utils.units`.

### Type Hints

All public functions must have type hints for parameters and return values:

```python
def get_impact_factor(bridge_type: str, span_m: float, vehicle: VehicleType) -> float:
    ...
```

### Docstrings

Use Google-style docstrings with `Args:` and `Returns:` sections:

```python
def initial_sizing(span: float, moment: float) -> dict:
    """Compute preliminary girder dimensions.

    Args:
        span: Effective span in mm
        moment: Design bending moment in kN·m

    Returns:
        Dictionary with 'web_depth', 'web_thickness', 'flange_width', 'flange_thickness'
    """
```

## Adding a New Bridge Type

1. Create a new package under `src/osdagbridge/core/bridge_types/<type_name>/`
2. Implement the standard module set:
   - `dto.py` — Input/output data transfer objects (use Pydantic)
   - `initial_sizing.py` — Preliminary sizing from empirical rules
   - `analyser.py` — Structural analysis orchestration
   - `designer.py` — Design checks per applicable codes
   - `cad_generator.py` — Geometry generation
   - `report_generator.py` — Report formatting
3. Add tests under `tests/unit/`
4. Update `__init__.py` exports

## Adding a New Code Module

1. Create the module under `src/osdagbridge/core/utils/codes/`
2. Register it in `registry.py`
3. Export key functions from `codes/__init__.py`
4. Add comprehensive tests

## Questions?

Open an issue on the repository for any questions about contributing.
