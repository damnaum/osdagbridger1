# OsdagBridge

> **Alpha (v0.2.x)** — Plate girder workflow works end-to-end.
> Box girder and truss are placeholder stubs. Desktop and web
> interfaces exist as scaffolding only.

OsdagBridge is the bridge-design arm of the Osdag ecosystem.
It handles analysis and design of steel highway bridges to Indian
Standards, with a single Python core shared by the CLI, a PySide6
desktop app, and a Django + React web front-end.

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

### How the core is organised
All number-crunching lives in `osdagbridge.core`.  The CLI, desktop, and web
layers are thin shells that call the same design functions underneath.

### Bridge-type plugin system
Each bridge type ships with:
- DTO (input model schema)
- Initial sizing routines
- Structural analysis configuration
- Design and code-check modules
- CAD geometry generation
- Report generation utilities

### Shared structural components
Common elements sit in `bridge_components/`:
- Girders  
- Decks  
- Crash barriers  
- Pedestals  
- Piers  
- Foundations  
- Piles and pile caps  

Components are reused across different bridge types.

### Solver back-ends
Three analysis engines are supported:
- Native lightweight FEM solver  
- OpenSeesPy  
- OspGrillage  

You can switch solvers at run-time; the native one is always available.

### Indian design codes
Bundled under `core/utils/codes/`:
- IRC:6–2017  
- IRC:22–2015  
- IRC:24–2010  

These provide vehicle loads, load combinations, material factors, and
code-level checks.

---

## Layout

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

- [ ] **v0.3** — Box girder sizing and design
- [ ] **v0.3** — Truss bridge sizing and design
- [ ] **v0.4** — Desktop GUI (PySide6) with proper forms
- [ ] **v0.4** — LaTeX / PDF report export
- [ ] **v0.5** — Django REST back-end and React front-end
- [ ] **v0.5** — OpenSees / OspGrillage solver wiring
- [ ] **v0.6** — Seismic analysis to IRC:6 seismic clauses

---

## Acknowledgements

OsdagBridge is part of the wider Osdag initiative — open-source tools
for steel design in education, research, and practice.

---

## License

This project is licensed under the MIT License.  
See the `LICENSE` file for full details.
