# User Guide

> **Alpha Release** — Only the plate girder workflow is fully functional.
> Box girder and truss modules are stubs.

## Installation

### From Source

```bash
git clone https://github.com/haanmain/bridge.git
cd bridge
pip install -e .
```

### Optional Extras

```bash
# Advanced solvers
pip install -e ".[opensees]"
pip install -e ".[ospgrillage]"

# Desktop GUI (planned)
pip install -e ".[desktop]"

# Report generation (LaTeX/PDF)
pip install -e ".[report]"
```

## CLI Usage

### Show Version

```bash
osdagbridge --version
```

### Show Available Modules

```bash
osdagbridge info
```

### Run Analysis

```bash
osdagbridge analyze examples/plate_girder/example_basic.yaml
```

With a specific solver:

```bash
osdagbridge analyze input.yaml --solver native
```

Save output to a JSON file:

```bash
osdagbridge analyze input.yaml -o results.json
```

### Generate Report

```bash
osdagbridge report input.yaml output_report.txt --format text
```

The report command runs the full design workflow and writes a formatted
calculation sheet to the output file.

## YAML Input Format

```yaml
bridge_type: plate_girder
input:
  # Project identification
  project_name: "NH-44 ROB"         # required
  bridge_name: "Km 245+500 ROB"     # required
  chainage: "km 245+500"            # optional

  # Geometry
  effective_span: 30000             # mm (required)
  span_type: simply_supported       # default
  carriageway_width: 7500           # mm
  num_lanes: 2
  footpath_width: 0                 # mm

  # Girders
  num_girders: 2                    # required, >= 2
  girder_spacing: 3000              # mm (required)

  # Materials
  steel_grade: E250A                # see table below
  concrete_grade: M30               # for composite (optional)

  # Loading
  live_load_class: CLASS_A          # CLASS_A | CLASS_70R | CLASS_AA
  num_lanes_loaded: 2
  wearing_coat_thickness: 75        # mm
  crash_barrier_load: 10.0          # kN/m

  # Optional overrides (omit for auto-sizing)
  # web_depth: 1800
  # web_thickness: 12
  # flange_width: 500
  # flange_thickness: 25

  # Seismic
  include_seismic: false
```

### Steel Grades (IS 2062)

| Grade | fy (MPa) | fu (MPa) |
|-------|----------|----------|
| E250A | 250 | 410 |
| E250B | 250 | 410 |
| E300 | 300 | 440 |
| E350 | 350 | 490 |
| E410 | 410 | 540 |
| E450 | 450 | 570 |

### Live Load Classes (IRC:6-2017)

| Class | Typical use |
|-------|-------------|
| CLASS_A | Normal highway bridges |
| CLASS_70R | Heavy loading (NH / expressway) |
| CLASS_AA | Urban / heavy traffic |

## Design Workflow

When you run `osdagbridge analyze`, the following steps are executed
automatically:

1. **Input validation** — Pydantic validates ranges, grades, and
   cross-references.
2. **Initial sizing** — if girder dimensions are not specified, they are
   estimated from span-to-depth ratios for the given load class.
3. **Section properties** — area, I, Z, section class (IS 800:2007 Table 2).
4. **Dead loads** — self-weight, deck slab, wearing coat, crash barriers.
5. **Live-load analysis** — influence-line-based moving-load sweep for the
   chosen IRC vehicle class, including impact factor.
6. **Factored forces** — ULS combination: 1.35 × DL + 1.50 × LL.
7. **Capacity checks** — moment (§ 8.2), LTB (§ 8.2.2), shear (§ 8.4),
   deflection (IRC:24 L/600), web bearing (§ 8.7.4).
8. **Utilisation ratios** — moment and shear ratios; overall PASS / FAIL.

## Interpreting Results

### Section Properties

| Key | Description |
|-----|-------------|
| `total_depth_mm` | Overall girder depth |
| `section_class` | plastic / compact / semi-compact / slender |
| `Ixx_mm4` | Second moment of area |
| `Zp_mm3` | Plastic section modulus |

### Design Checks

| Key | Description |
|-----|-------------|
| `moment_capacity_governing_kNm` | Governing Md (kN·m) |
| `design_shear_capacity_kN` | Governing Vd (kN) |
| `total_deflection_mm` | Midspan deflection |

### Utilisation

| Key | Meaning |
|-----|---------|
| `moment_ratio` | Mu / Md (should be ≤ 1.0) |
| `shear_ratio` | Vu / Vd (should be ≤ 1.0) |
| `status` | PASS if all checks pass |

## Examples

| File | Description |
|------|-------------|
| `examples/plate_girder/example_basic.yaml` | 30 m span, E250A, Class A |
| `examples/plate_girder/verification_case_01.yaml` | 20 m span, E250A, Class A |
| `examples/plate_girder/verification_case_02.yaml` | 25 m span, E350, 70R |

## Desktop Application (Planned)

```bash
python -m osdagbridge.desktop
```

Requires the `desktop` extra.  Currently prints a placeholder message.

## Web Application (Planned)

The Django/React interface is under development.  See `web/` for stubs.
