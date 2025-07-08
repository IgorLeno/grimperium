# AGENT.md - Grimperium Development Guide

> **Notice:**  
> This file (`AGENT.md`) is intended exclusively for AMP (ampcode) sessions.  
> Do **not** use or reference this file in Claude Code agent sessions.  
> For Claude Code context and memory, refer to `CLAUDE.md` in this directory.

## Commands
- **Run single molecule**: `python main.py run-single --name "ethanol"` or `python main.py run-single --smiles "CCO"`
- **Run batch processing**: `python main.py run-batch molecules.txt`
- **System diagnostics**: `python main.py info` (verify setup and dependencies)
- **Progress reports**: `python main.py report --detailed --missing 10`
- **Interactive mode**: `python main.py` (questionary-based menu)
- **Test single test**: `pytest grimperium/tests/test_pipeline_orchestrator.py::TestPipelineOrchestrator::test_process_single_molecule_success -v`
- **Run all tests**: `pytest grimperium/tests/ -v`

## Architecture
- **Entry point**: `main.py` - CLI with Typer, Rich, and Questionary
- **Services**: PubChem API, OpenBabel conversion, CREST/MOPAC calculation, database operations
- **Data flow**: PubChem → CREST → MOPAC → CSV database
- **External deps**: `crest`, `mopac`, `obabel` chemistry tools
- **Configuration**: `config.yaml` - executables, keywords, paths
- **Database**: Thread-safe CSV operations with FileLock

## Code Style
- **Architecture**: Service-oriented with base classes in `utils/base_service.py`
- **Data validation**: Pydantic models in `grimperium/core/molecule.py`
- **Error handling**: Centralized in `utils/error_handler.py` with comprehensive logging
- **Testing**: pytest with mocked external dependencies (chemistry tools)
- **Environment**: Conda with Python 3.9+, setup via `setup_environment.sh`
- **File structure**: `repository/molecule_name/` workspace, `data/` for CSV databases

---
## Agent Context Separation

- `AGENT.md`: Used **only** by AMP (ampcode) for context and workflow memory.
- `CLAUDE.md`: Used **only** by Claude Code.
- Do not share or duplicate instructions between these files unless necessary for interoperability.
