# Contributing to OsdagBridge

Thanks for wanting to help! Here's how to get going.

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

- Write clear, typed, documented code
- Stick to the patterns already in the codebase
- Lines should be ≤ 100 characters (ruff will tell you if you slip)

### 5. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=osdagbridge --cov-report=term-missing

# Run a specific test file
pytest tests/unit/test_designer.py -v
```

Every test must pass before you open a PR.

### 6. Run Linting

```bash
ruff check src/ tests/
```

Fix any issues reported by ruff before submitting.

### 7. Open a Pull Request

- Push your branch to your fork
- Open a PR against `main`
- Describe what you changed and why
- Link relevant issues if any

## Code Standards

### Cite your clauses

**Every engineering formula must reference the exact clause** from the
relevant standard. For example:

```python
def calculate_shear_capacity(d, tw, fy):
    """Plastic shear capacity per IS 800:2007 Clause 8.4.1."""
    Av = d * tw
    Vd = Av * fy / (math.sqrt(3) * gamma_m0)  # IS 800 Cl 8.4.1
    return Vd
```

### Applicable standards

- **IS 800:2007** — General Construction in Steel (Limit State Method)
- **IRC:6-2017** — Standard Specifications for Road Bridges, Section II: Loads and Load Combinations
- **IRC:22-2015** — Standard Specifications for Road Bridges, Section VI: Composite Construction
- **IRC:24-2010** — Standard Specifications for Road Bridges, Section V: Steel Road Bridges

### Units

Everything internal runs in a single set of units:

| Quantity    | Unit  |
|-------------|-------|
| Length      | mm    |
| Force       | kN    |
| Stress      | MPa   |
| Moment      | kN·m  |

Conversion helpers are available in `osdagbridge.core.utils.units`.

### Type hints

All public functions need type annotations:

```python
def get_impact_factor(bridge_type: str, span_m: float, vehicle: VehicleType) -> float:
    ...
```

### Docstrings

Keep them concise — a one-liner is fine for simple helpers.
For anything non-trivial, a short paragraph plus `Args:` / `Returns:`
is plenty:

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

## Adding a new bridge type

1. Create `src/osdagbridge/core/bridge_types/<type_name>/`
2. Write the standard set of modules:
   - `dto.py` — Input/output data transfer objects (use Pydantic)
   - `initial_sizing.py` — Preliminary sizing from empirical rules
   - `analyser.py` — Structural analysis orchestration
   - `designer.py` — Design checks per applicable codes
   - `cad_generator.py` — Geometry generation
   - `report_generator.py` — Report formatting
3. Add tests under `tests/unit/`
4. Update `__init__.py` exports

## Adding a new code module

1. Drop a new file into `src/osdagbridge/core/utils/codes/`
2. Register it in `registry.py`
3. Re-export key functions from `codes/__init__.py`
4. Write thorough tests

## Questions?

Open an issue — we're happy to help.
