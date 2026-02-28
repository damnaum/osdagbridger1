# OsdagBridge

> **Alpha (v0.1.x)** — The plate girder workflow is functional end-to-end.
> Box girder and truss modules are stubs.  Desktop GUI and Web interface
> are planned but not yet implemented.

OsdagBridge is a modular, shared-core software plugin for the analysis and
design of steel bridges within the Osdag ecosystem.  It supports Desktop
(PySide6), Web (Django + React), and CLI interfaces through a unified Python
core.

---

## Key Features

| Feature | Status |
|---------|--------|
| Plate Girder Bridge design (IS 800:2007) | **Working** |
| IRC:6-2017 live loads & moving-load analysis | **Working** |
| IRC:22-2015 composite helpers | **Working** |
| IRC:24-2010 deflection limits | **Working** |
| CLI (`osdagbridge analyze` / `report`) | **Working** |
| Box Girder / Truss | Stub |
| Desktop GUI (PySide6) | Planned |
| Web App (Django + React) | Planned |

### Shared Core Architecture
All numerical logic lives in `osdagbridge.core`.  The CLI, desktop, and web
layers are thin wrappers that call into exactly the same design functions.

### Modular Bridge-Type System
Each bridge type includes:
- DTO (input model schema)
- Initial sizing routines
- Structural analysis configuration
- Design and code-check modules
- CAD geometry generation
- Report generation utilities

### Reusable Bridge Components
Common structural elements are defined in `bridge_components/`:
- Girders  
- Decks  
- Crash barriers  
- Pedestals  
- Piers  
- Foundations  
- Piles and pile caps  

Components are shared across multiple bridge types.

### Multi-Solver Analysis Support
Multiple analysis backends are supported:
- Native lightweight FEM solver  
- OpenSeesPy  
- OspGrillage  

Solvers are switchable at runtime via adapters.

### Integrated Indian Standards
Included under `core/utils/codes/`:
- IRC:6–2017  
- IRC:22–2015  
- IRC:24–2010  

These modules provide load models, combinations, material factors, and code checks.

---

## Project Structure

```
bridge/
├── docs/                         # Architecture, developer & user guides
├── examples/plate_girder/        # YAML input examples
├── tests/
│   ├── unit/                     # Unit tests
│   └── integration/              # Integration & verification tests
├── web/
│   ├── backend/                  # Django REST backend
│   └── frontend/                 # React frontend
└── src/
    └── osdagbridge/
        ├── cli/                  # Command-line interface
        ├── desktop/              # PySide6 GUI
        └── core/
            ├── bridge_types/     # Plate girder, box girder, truss
            │   └── plate_girder/ # DTO, designer, analyser, CAD, reports
            ├── bridge_components/# Reusable structural components
            │   ├── foundation/   # Pile, pile cap
            │   ├── sub_structure/ # Pedestal, pier, pier cap
            │   └── super_structure/ # Crash barrier, deck, girder
            ├── loads/            # Vehicle loads, moving load, placement
            ├── solvers/          # Native, OpenSees, OspGrillage adapters
            ├── reports/          # Report generation (text, LaTeX)
            └── utils/
                ├── codes/        # IRC:6, IRC:22, IRC:24, registry
                ├── logger.py
                ├── units.py
                └── validation.py
```

---

## Installation

Clone the repository:

```bash
git clone https://github.com/haanmain/bridge.git
cd bridge
```

Install in editable mode:

```bash
pip install -e .
```

---

## Usage

### Command-Line Interface

Run an analysis:

```bash
osdagbridge analyze project.yaml --solver native
```

Generate a report:

```bash
osdagbridge report project.yaml report.pdf
```

### Desktop Application

```bash
python -m osdagbridge.desktop
```

### Web Application

Backend:

```bash
python src/osdagbridge/web/backend/manage.py runserver
```

Frontend:

```bash
cd src/osdagbridge/web/frontend
npm install
npm start
```

---

## Testing

Run the complete test suite:

```bash
pytest -q
```

Continuous integration runs automatically through GitHub Actions (`.github/workflows/ci.yml`).

---

## Development Guidelines

### Key Code Locations
- Core logic: `src/osdagbridge/core/`
- Codes & standards: `src/osdagbridge/core/utils/codes/`
- Bridge types: `src/osdagbridge/core/bridge_types/`
- Components: `src/osdagbridge/core/bridge_components/`
- CLI: `src/osdagbridge/cli/`
- Desktop GUI: `src/osdagbridge/desktop/`
- Web: `web/backend/` and `web/frontend/`

### Contribution Workflow
1. Fork the repository  
2. Create a feature branch  
3. Ensure all tests pass (`pytest`)  
4. Submit a pull request

---

## Roadmap

- [ ] **v0.2** — Box girder initial sizing and design
- [ ] **v0.2** — Truss bridge initial sizing and design
- [ ] **v0.3** — Desktop GUI (PySide6) with form-based input
- [ ] **v0.3** — LaTeX / PDF report generation
- [ ] **v0.4** — Web backend (Django REST) and React frontend
- [ ] **v0.4** — OpenSees / OspGrillage solver integration
- [ ] **v0.5** — Seismic analysis (IRC:6 seismic clauses)

---

## Acknowledgements

OsdagBridge is part of the Osdag project, promoting open-source tools for steel design education, research, and practice.

---

## License

This project is licensed under the MIT License.  
See the `LICENSE` file for full details.
