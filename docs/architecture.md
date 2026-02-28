# OsdagBridge Architecture

> **Status**: Alpha (v0.2.x) — plate girder is working; box girder
> and truss are stubs waiting for implementation.

## Overview

OsdagBridge keeps all the engineering maths in one shared core so that
three different front-ends (CLI, desktop PySide6, web Django + React)
can call into the same design functions without duplicating logic.

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│     CLI      │  │   Desktop   │  │     Web      │
│  (argparse)  │  │  (PySide6)  │  │(Django+React)│
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └────────────┬────┴────┬────────────┘
                    │         │
              ┌─────▼─────────▼──────┐
              │     osdagbridge.core  │
              │  (all engineering     │
              │   logic lives here)   │
              └───────────┬──────────┘
                          │
       ┌──────────┬───────┼───────┬──────────┐
       │          │       │       │          │
  bridge_types  loads  solvers  reports  utils/codes
```

## Data Flow

```
YAML / GUI Input
       │
       ▼
   DTO Validation  ─── PlateGirderInput (Pydantic)
       │
       ▼
   Initial Sizing  ─── Empirical rules (span/depth, slenderness)
       │
       ▼
   Dead-Load Calc  ─── Self-weight, deck, wearing coat, barriers
       │
       ▼
   Live-Load Analysis ── Moving-load engine (influence-line sweep)
       │
       ▼
   Factored Forces ─── γ_DL × DL  +  γ_LL × LL  (IRC:6 Table 1)
       │
       ▼
   Design Checks   ─── IS 800:2007 (moment, shear, LTB, deflection)
       │
       ▼
   Report / JSON   ─── Text report or JSON file
```

1. **Input** — a YAML file or GUI form provides project parameters.
2. **DTO Validation** — `PlateGirderInput` (Pydantic BaseModel) validates
   ranges, steel grades, and cross-references.
3. **Initial Sizing** — empirical span-to-depth rules generate starting
   dimensions when the user does not supply them.
4. **Dead-Load Calculation** — self-weight, deck slab, wearing coat,
   cross-beams, and crash barriers are summed per girder.
5. **Live-Load Analysis** — a moving-load sweep (influence-line method)
   finds critical BM and SF envelopes for the specified IRC vehicle.
6. **Factored Forces** — ULS load factors (γ_DL = 1.35, γ_LL = 1.50) are
   applied per IRC:6-2017 Table 1.
7. **Design Checks** — IS 800:2007 checks for moment capacity (§ 8.2),
   shear (§ 8.4), lateral-torsional buckling (§ 8.2.2), web bearing
   (§ 8.7.4), and deflection (IRC:24 L/600).
8. **Output** — results returned as a nested dict containing utilisation
   ratios and PASS/FAIL status; optionally formatted as a text report.

## Bridge Types — Plugin Pattern

Each bridge type lives in its own package under `core/bridge_types/`:

```
core/bridge_types/
├── plate_girder/           ← fully implemented
│   ├── dto.py              # Input/output data models (Pydantic)
│   ├── initial_sizing.py   # Preliminary sizing from empirical rules
│   ├── analyser.py         # Load computation → solver orchestration
│   ├── designer.py         # IS 800:2007 design checks
│   ├── cad_generator.py    # 2D cross-section polygon
│   └── report_generator.py # Bridge-type-specific report stub
├── box_girder/             ← stub
└── truss/                  ← stub
```

To add a new bridge type (e.g. cable-stayed):

1. Create `core/bridge_types/cable_stayed/` with the same 6-module structure.
2. Define a Pydantic DTO with validated input parameters.
3. Implement analysis, design checks, and report formatting.
4. Register the type in the CLI dispatch logic (`cli/commands.py`).

## Solver Adapter Pattern

Solvers are interchangeable back-ends:

| Solver | Module | Status |
|--------|--------|--------|
| native | `native_solver.py` | Working — lightweight beam solver |
| OpenSees | `opensees_adapter.py` | Optional — wraps OpenSeesPy |
| OspGrillage | `ospgrillage_adapter.py` | Optional — grillage analysis |

Each adapter exposes a consistent interface:

```python
class NativeSolver:
    @property
    def is_available(self) -> bool: ...
    def analyze_simply_supported(self, span, EI, loads) -> dict: ...
```

The native solver is always available; OpenSees and OspGrillage are optional
`pip install` extras that degrade gracefully when absent.

## Indian Design Codes

Pure-function modules under `core/utils/codes/`:

| Module | Standard | Key content |
|--------|----------|-------------|
| `irc6_2017.py` | IRC:6-2017 | Vehicle loads, impact factors, lane distribution |
| `irc22_2015.py` | IRC:22-2015 | Composite section modular ratios, effective width |
| `irc24_2010.py` | IRC:24-2010 | Deflection limits, web panel shear buckling |
| `load_combinations.py` | IRC:6 + IS 800 | All 6 limit-state load combinations |
| `registry.py` | — | Auto-registration and lookup by name |

New codes are added by creating a module and calling `register_code()`.

## Bridge Components

Reusable structural components shared across bridge types:

```
core/bridge_components/
├── foundation/          # Pile, pile cap geometry & capacity checks
├── sub_structure/       # Pedestal, pier, pier cap
└── super_structure/     # Crash barrier, deck, girder
```

Each component is a `@dataclass` with geometry helpers and basic capacity
checks.  Components are independent of any particular bridge type.

## Unit Convention

All internal calculations use a consistent unit system:

| Quantity | Unit |
|----------|------|
| Length | mm |
| Force | kN |
| Stress | MPa (N/mm²) |
| Moment | kN·m |

Conversion helpers live in `core/utils/units.py`.

## Error Handling

Custom exception hierarchy in `core/exceptions.py`:

| Exception | Purpose |
|-----------|---------|
| `OsdagError` | Base for all OsdagBridge errors |
| `DesignFailedError` | Capacity < demand |
| `InputValidationError` | Invalid parameters |
| `SolverError` | Solver failure |

## Logging

Structured logging via `core/utils/logger.py`.  The default handler writes
to `stderr` at `WARNING` level; use `configure_logging(level="DEBUG")` for
verbose output during development.
