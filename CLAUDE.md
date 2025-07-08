# CLAUDE.md - Grimperium v2 Context

## Project Overview

**Grimperium v2** is a command-line interface tool for computational chemistry workflow automation. It orchestrates the integration between PubChem, CREST, and MOPAC to automate the generation of molecular thermodynamic data.

### Core Purpose
- Automate computational chemistry workflows
- Process molecules through: PubChem → CREST → MOPAC → Database
- Generate thermodynamic data for molecular research
- Provide both interactive and batch processing modes

---

## Architecture & Design Patterns

### Design Philosophy
- **Modular Architecture**: Services with single responsibilities
- **Configuration-Driven**: External YAML configuration
- **Thread-Safe Operations**: FileLock for database operations
- **Error Handling**: Comprehensive error handling and logging
- **CLI-First**: Rich CLI interface with interactive mode

### Core Components

#### 1. Entry Point
- **`main.py`**: CLI entry point with Typer, interactive menu with Questionary
- **Commands**: `run-single`, `run-batch`, `report`, `info`
- **Interactive Mode**: Menu-driven interface for user-friendly operation

#### 2. Service Layer (`grimperium/services/`)
- **`pubchem_service.py`**: PubChem API integration
- **`conversion_service.py`**: OpenBabel format conversions
- **`calculation_service.py`**: CREST/MOPAC execution and parsing
- **`database_service.py`**: Thread-safe CSV operations with Pandas
- **`pipeline_orchestrator.py`**: Workflow coordination
- **`analysis_service.py`**: Progress reports and analysis

#### 3. Domain Models (`grimperium/core/`)
- **`molecule.py`**: Pydantic-based Molecule class for data validation

#### 4. Utilities (`grimperium/utils/`)
- **`config_manager.py`**: YAML configuration loading and validation
- **`base_service.py`**: Base service class
- **`error_handler.py`**: Centralized error handling
- **`file_utils.py`**: File manipulation utilities
- **`subprocess_utils.py`**: Subprocess execution utilities

---

## Configuration System

### config.yaml Structure
```yaml
executables:
  crest: 'crest'
  mopac: 'mopac' 
  obabel: 'obabel'

mopac_keywords: 'PM7 EF PRECISE GNORM=0.01 NOINTER GRAPHF VECTORS MMOK CYCLES=20000'
crest_keywords: '--gfn2'
repository_base_path: 'repository'

logging:
  log_file: 'logs/grim_details.log'
  console_level: 'INFO'
  file_level: 'DEBUG'

database:
  cbs_db_path: 'data/thermo_cbs.csv'
  pm7_db_path: 'data/thermo_pm7.csv'
```

### Configuration Validation
- Executable paths are validated on startup
- Configuration loading includes error handling
- Environment-specific settings supported

---

## Data Flow & Pipeline

### Pipeline Stages
1. **Input Processing**: Handle molecule name or SMILES
2. **PubChem Query**: Fetch 3D structure (SDF format)
3. **Format Conversion**: SDF → XYZ (OpenBabel)
4. **Conformational Search**: XYZ → optimized geometry (CREST)
5. **Quantum Calculation**: PM7 thermodynamic properties (MOPAC)
6. **Data Storage**: Results saved to CSV database

### File Organization
```
repository/
├── molecule_name/
│   ├── molecule.sdf      # PubChem structure
│   ├── molecule.xyz      # Converted coordinates
│   ├── crest_output/     # CREST results
│   └── mopac_output/     # MOPAC calculations
```

### Database Schema
- **CBS Database**: Reference thermodynamic data
- **PM7 Database**: Calculated results with columns:
  - `smiles`: Canonical SMILES
  - `xyz`: Optimized coordinates
  - `H298_pm7`: Enthalpy at 298K (kcal/mol)
  - `S298_pm7`: Entropy at 298K (cal/mol·K)
  - Additional thermodynamic properties

---

## Key Dependencies

### External Programs
- **CREST**: Conformational search (`crest --gfn2`)
- **MOPAC**: Quantum calculations (`mopac` with PM7)
- **OpenBabel**: Format conversions (`obabel`)

### Python Dependencies
- **typer**: CLI framework
- **rich**: Terminal formatting
- **questionary**: Interactive prompts
- **pandas**: Data manipulation
- **pydantic**: Data validation
- **pyyaml**: Configuration parsing
- **pubchempy**: PubChem API client
- **filelock**: Thread-safe file operations

---

## Development Guidelines

### Code Organization
- Follow service-oriented architecture
- Use Pydantic for data validation
- Implement comprehensive error handling
- Include detailed logging
- Write unit tests with mocks for external dependencies

### Testing Strategy
- Mock external program calls (CREST, MOPAC, OpenBabel)
- Test service logic independently
- Use pytest for test framework
- Focus on pipeline orchestration testing

### Error Handling
- Service-specific error handling
- Centralized error logging
- Graceful degradation where possible
- User-friendly error messages

---

## Usage Patterns

### Interactive Mode
```bash
python main.py
# Launches questionary-based interactive menu
```

### Direct Commands
```bash
# Single molecule processing
python main.py run-single --name "ethanol"
python main.py run-single --smiles "CCO"

# Batch processing
python main.py run-batch molecules.txt

# System diagnostics
python main.py info

# Progress reporting
python main.py report --detailed --missing 10
```

### Workflow Commands
- Use `python main.py info` to verify system setup
- Check `logs/grim_details.log` for detailed execution logs
- Monitor `data/thermo_pm7.csv` for calculation results

---

## File Structure Reference

```
grimperium/
├── grimperium/
│   ├── core/molecule.py
│   ├── services/
│   │   ├── pubchem_service.py
│   │   ├── conversion_service.py
│   │   ├── calculation_service.py
│   │   ├── database_service.py
│   │   ├── pipeline_orchestrator.py
│   │   └── analysis_service.py
│   ├── utils/
│   │   ├── config_manager.py
│   │   ├── base_service.py
│   │   ├── error_handler.py
│   │   ├── file_utils.py
│   │   └── subprocess_utils.py
│   └── tests/
├── docs/
│   ├── README.md
│   ├── architecture.md
│   ├── database_schema.md
│   └── project_structure.md
├── data/                    # CSV databases
├── repository/              # Calculation workspace
├── logs/                    # Application logs
├── config.yaml             # Main configuration
└── main.py                 # CLI entry point
```

---

## Common Development Tasks

### Adding New Services
1. Inherit from `BaseService` in `utils/base_service.py`
2. Implement error handling and logging
3. Add service to `pipeline_orchestrator.py`
4. Update configuration if needed
5. Write unit tests

### Modifying Pipeline
1. Update `pipeline_orchestrator.py`
2. Modify service interactions
3. Update database schema if needed
4. Test with single and batch modes

### Configuration Changes
1. Update `config.yaml` structure
2. Modify `config_manager.py` validation
3. Update documentation
4. Test with `python main.py info`

---

## Performance Considerations

### Database Operations
- Use FileLock for thread-safe CSV writes
- Batch database operations where possible
- Check for existing entries before processing

### External Program Execution
- Implement timeouts for subprocess calls
- Handle program failures gracefully
- Clean up temporary files

### Memory Management
- Process large batches in chunks
- Clean up intermediate files
- Monitor log file sizes

---

## Troubleshooting Guide

### Common Issues
1. **Missing Executables**: Run `python main.py info` to check
2. **Configuration Errors**: Validate `config.yaml` syntax
3. **Database Lock Issues**: Check for stale `.lock` files
4. **Log File Growth**: Monitor `logs/grim_details.log` size

### Debug Commands
```bash
# System diagnostics
python main.py info

# Detailed progress report
python main.py report --detailed

# Check log files
tail -f logs/grim_details.log
```

---

## Project Context for New Sessions

When starting a new Claude session on this project:

1. **Project Type**: Computational chemistry automation tool
2. **Primary Language**: Python 3.9+
3. **Architecture**: Service-oriented with CLI interface
4. **Key Technologies**: Typer, Rich, Pandas, Pydantic
5. **External Dependencies**: CREST, MOPAC, OpenBabel
6. **Data Storage**: CSV files with thread-safe operations
7. **Testing**: pytest with mocked external dependencies

### Quick Start Commands
```bash
# Verify project setup
python main.py info

# Run interactive mode
python main.py

# Test single molecule
python main.py run-single --name "water"

# Check progress
python main.py report
```

This context should provide sufficient information for any new Claude session to understand the project structure, purpose, and development patterns.