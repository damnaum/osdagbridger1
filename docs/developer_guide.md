# Developer Guide

## Prerequisites

- Python 3.9, 3.10, 3.11, or 3.12
- Git

## Installation

```bash
git clone https://github.com/haanmain/bridge.git
cd bridge
pip install -e ".[dev]"
```

This installs the package in editable mode along with development tools:

| Tool | Purpose |
|------|---------|
| pytest | Test runner |
| pytest-cov | Coverage reporting |
| ruff | Linter and formatter |
| mypy | Static type checker |

## Running Tests

```bash
# All tests (fast, default)
pytest

# Verbose with coverage
pytest -v --cov=osdagbridge --cov-report=term-missing

# Single file
pytest tests/unit/test_designer.py

# By keyword
pytest -k "shear"

# Only slow/integration (requires marker)
pytest -m integration
```

All tests **must** pass before submitting code.

## Linting

```bash
# Check for lint issues
ruff check src/ tests/

# Auto-fix what can be fixed
ruff check src/ tests/ --fix
```

Configuration is in `pyproject.toml`:
- Line length: 100 characters
- Target: Python 3.9

## Type Checking

```bash
mypy src/osdagbridge/
```

All public functions should have type hints.

## Project Layout

```
src/osdagbridge/
├── __init__.py                    # Package version
├── cli/                           # Command-line interface
│   ├── __main__.py                # Entry point (argparse)
│   └── commands.py                # Command implementations
├── desktop/                       # PySide6 GUI (planned)
└── core/                          # All engineering logic
    ├── exceptions.py              # Custom exception hierarchy
    ├── bridge_types/              # Per-bridge-type packages
    │   └── plate_girder/          # DTO, designer, analyser, CAD, report
    ├── bridge_components/         # Reusable structural elements
    │   ├── foundation/            # Pile, pile cap
    │   ├── sub_structure/         # Pedestal, pier, pier cap
    │   └── super_structure/       # Crash barrier, deck, girder
    ├── loads/                     # Vehicle loads, moving load analysis
    ├── solvers/                   # Native, OpenSees, OspGrillage
    ├── reports/                   # Report generation
    └── utils/
        ├── codes/                 # IRC/IS code implementations
        ├── logger.py              # Logging setup
        ├── units.py               # Unit conversions
        └── validation.py          # Input validation helpers
```

## Adding a New Bridge Type

1. Create `src/osdagbridge/core/bridge_types/<type_name>/`.
2. Implement the standard 6-module set:

| Module | Purpose |
|--------|---------|
| `dto.py` | Pydantic input model + output dataclass |
| `initial_sizing.py` | Preliminary sizing from empirical rules |
| `analyser.py` | Load computation → solver orchestration |
| `designer.py` | Design checks per applicable codes |
| `cad_generator.py` | 2D/3D geometry coordinates |
| `report_generator.py` | Formatted output report |

3. Register in the CLI dispatch (`cli/commands.py`).
4. Write unit tests under `tests/unit/`.
5. Update exports in `__init__.py`.

## Adding a New Code Module

1. Create `src/osdagbridge/core/utils/codes/<code_name>.py`.
2. Implement functions as pure functions; reference clause numbers:
   ```python
   def get_deflection_limit(span: float) -> float:
       """Allowable deflection per IRC:24-2010 Clause 504.5."""
       return span / 600
   ```
3. Register via `register_code("IRC:24-2010", module)` in `registry.py`.
4. Write comprehensive tests.

## Engineering Code Standards

**Every structural formula must cite its source clause.**

```python
# IS 800:2007 Clause 8.4.1
Vd = Av * fy / (math.sqrt(3) * gamma_m0)
```

Acceptable references:
- IS 800:2007 — General Construction in Steel
- IRC:6-2017 — Loads and Load Combinations
- IRC:22-2015 — Composite Construction
- IRC:24-2010 — Steel Road Bridges

## Unit Convention

| Quantity | Unit | Example |
|----------|------|---------|
| Length | mm | `effective_span = 30000` |
| Force | kN | `axle_load = 114` |
| Stress | MPa | `fy = 250` |
| Moment | kN·m | `Md = 4500.0` |

Use helpers in `osdagbridge.core.utils.units` for conversions.

## CI/CD

GitHub Actions (`.github/workflows/ci.yml`) runs on every push and PR to
`main`:

- Lint with ruff (including format check)
- Tests on Python 3.9, 3.10, 3.11, 3.12
- Coverage report uploaded as artifact

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for the full contribution workflow.
