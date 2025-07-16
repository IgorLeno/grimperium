CLAUDE.md - Grimperium v2 Project Context

Notice: Multi-Agent Context Separation
This file is intended exclusively for Claude Code agent sessions for the Grimperium project.
Do not use or reference this file in AMP (ampcode) agent sessions.
For AMP context, always use AGENT.md in the project directory.

Quick Context
Grimperium v2 is a Python CLI tool for computational chemistry workflow automation that processes molecules through: PubChem → CREST → MOPAC → Database pipeline.

Tech Stack & Architecture
Core Technologies: Python 3.9+ | Typer + Rich + Questionary | Pandas + Pydantic | External: CREST, MOPAC, OpenBabel

Architecture: Service-oriented modular design with clear separation of responsibilities

Pipeline: PubChem API → format conversion → conformational search → quantum calculations → CSV storage

Config: YAML-driven (config.yaml) with validation

Storage: Thread-safe CSV operations with FileLock

CLI: Interactive menu + direct commands

Essential Commands
bash
# System check (always run first)
python main.py info

# Single molecule processing
python main.py run-single --name "ethanol"
python main.py run-single --smiles "CCO"

# Batch processing
python main.py run-batch molecules.txt

# Progress analysis
python main.py report
python main.py report --detailed
python main.py report --missing 10

# Interactive mode
python main.py
Project Structure
text
grimperium/
├── grimperium/
│   ├── core/molecule.py          # Pydantic Molecule model
│   ├── services/                 # Business logic
│   │   ├── pubchem_service.py    # PubChem API integration
│   │   ├── conversion_service.py # OpenBabel format conversion
│   │   ├── calculation_service.py # CREST/MOPAC execution
│   │   ├── database_service.py   # Thread-safe CSV operations
│   │   ├── pipeline_orchestrator.py # Workflow coordination
│   │   └── analysis_service.py   # Progress reports
│   ├── utils/config_manager.py   # YAML config handling
│   └── tests/                    # Test suite
├── docs/                         # Project documentation
├── data/                         # CSV databases
├── repository/                   # Calculation workspace
├── logs/                         # Application logs
├── config.yaml                   # Main configuration
└── main.py                       # CLI entry point

# Key Development Patterns
Service Pattern
Inherit from BaseService in utils/base_service.py
Each service has single responsibility
Comprehensive error handling and logging
Use Pydantic for data validation

# Configuration
All external programs configured in config.yaml
Validation on startup via config_manager.py
Never hardcode paths or executable names

# Database Operations
Use database_service.py for all CSV operations
FileLock ensures thread-safe writes
Check for existing entries before processing

# Testing
Mock external programs (CREST, MOPAC, OpenBabel)
Use pytest with intelligent mocks
Test service logic independently
Critical Files & Locations

# Don't Touch:

Files in repository/ directory (calculation workspace)
Database files directly (data/*.csv)
External program paths without config update

# Essential for Development:

logs/grim_details.log - Detailed execution logs
config.yaml - External program configuration
main.py - CLI commands and interactive menu

Common Development Tasks

# Adding New Services:
Inherit from BaseService
Add to pipeline_orchestrator.py
Update config.yaml if needed
Write unit tests with mocks

# Debugging Issues:
Check python main.py info for system status
Review logs/grim_details.log for detailed errors
Test single molecules before batch processing

# Configuration Changes:

Update config.yaml structure

Modify config_manager.py validation

Test with python main.py info

Development Context
Project Focus: Academic/research chemistry automation
Data Flow: Molecule identifier → 3D structure → conformational search → quantum calculation → thermodynamic data
External Dependencies: Requires CREST, MOPAC, OpenBabel installed
Database Schema: CSV files with SMILES, coordinates, and calculated properties

This context provides sufficient information to understand the project structure, run diagnostics, and begin development tasks following the established patterns.

