#!/usr/bin/env python3
"""
Grimperium v2 - Computational Chemistry Workflow Automation Tool

This is the main entry point for the Grimperium application, which provides
automated workflows for computational chemistry calculations including
conformational search, quantum chemical calculations, and thermodynamic analysis.
"""

import logging
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer
import questionary
from rich import print as rich_print
from rich.console import Console
from rich.progress import (
    Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
)
from rich.panel import Panel
from rich.table import Table

from grimperium.utils.config_manager import load_config
from grimperium.services.pipeline_orchestrator import (
    process_single_molecule,
    validate_pipeline_setup
)
from grimperium.services.analysis_service import (
    generate_progress_report,
    get_detailed_database_analysis,
    find_missing_molecules
)

# Define project root for absolute path resolution
PROJECT_ROOT = Path(__file__).resolve().parent

# Initialize Rich console
console = Console()

app = typer.Typer(
    name="grimperium",
    help="Grimperium v2 - Computational Chemistry Workflow Automation Tool",
    add_completion=False,
)


def setup_logging(verbose: bool = False):
    """Setup logging configuration based on verbosity level."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


# BUSINESS LOGIC FUNCTIONS (DECOUPLED FROM UI)

def _execute_single_molecule_logic(
    identifier: str, identifier_type: str, config_file: str, verbose: bool = False
) -> bool:
    """
    Execute single molecule processing logic.

    Args:
        identifier: Molecule identifier (name or SMILES)
        identifier_type: Type of identifier ("name" or "SMILES")
        config_file: Path to configuration file
        verbose: Enable verbose output

    Returns:
        bool: True if processing was successful, False otherwise
    """
    setup_logging(verbose)

    # Display welcome message
    console.print(Panel.fit(
        "[bold blue]🧪 Grimperium v2[/bold blue]\n"
        "[cyan]Computational Chemistry Workflow Automation[/cyan]",
        border_style="blue"
    ))

    # Load configuration
    rich_print(f"[yellow]📋 Loading configuration from: {config_file}[/yellow]")
    config = load_config(config_file, PROJECT_ROOT)
    if not config:
        rich_print(f"[red]❌ Failed to load configuration from: {config_file}[/red]")
        return False

    # Validate pipeline setup
    rich_print("[yellow]🔧 Validating pipeline setup...[/yellow]")
    if not validate_pipeline_setup(config):
        rich_print("[red]❌ Pipeline setup validation failed[/red]")
        return False

    # Process the molecule
    rich_print(
        f"[green]🚀 Processing molecule ({identifier_type}): {identifier}[/green]"
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task("Processing molecule...", total=None)
        success = process_single_molecule(identifier, config)

    # Display results
    if success:
        rich_print(f"[green]✅ Successfully processed: {identifier}[/green]")
        rich_print("[green]🎉 Results saved to database![/green]")
        return True
    else:
        rich_print(f"[red]❌ Failed to process: {identifier}[/red]")
        rich_print("[red]💥 Check the logs for detailed error information[/red]")
        return False


def _execute_batch_logic(
    file_path: str, config_file: str, verbose: bool = False
) -> dict:
    """
    Execute batch processing logic.

    Args:
        file_path: Path to file containing molecule identifiers
        config_file: Path to configuration file
        verbose: Enable verbose output

    Returns:
        dict: Processing results with counts
    """
    setup_logging(verbose)

    # Display welcome message
    console.print(Panel.fit(
        "[bold blue]🧪 Grimperium v2 - Batch Mode[/bold blue]\n"
        "[cyan]Computational Chemistry Workflow Automation[/cyan]",
        border_style="blue"
    ))

    # Validate input file
    input_file = Path(file_path)
    if not input_file.exists():
        rich_print(f"[red]❌ Input file not found: {file_path}[/red]")
        return {"error": f"Input file not found: {file_path}"}

    # Load molecule identifiers
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            identifiers = [line.strip() for line in f if line.strip()]
    except Exception as e:
        rich_print(f"[red]❌ Error reading input file: {e}[/red]")
        return {"error": f"Error reading input file: {e}"}

    if not identifiers:
        rich_print(f"[red]❌ No molecule identifiers found in: {file_path}[/red]")
        return {"error": f"No molecule identifiers found in: {file_path}"}

    rich_print(f"[green]📄 Loaded {len(identifiers)} molecule identifiers[/green]")

    # Load configuration
    rich_print(f"[yellow]📋 Loading configuration from: {config_file}[/yellow]")
    config = load_config(config_file, PROJECT_ROOT)
    if not config:
        rich_print(f"[red]❌ Failed to load configuration from: {config_file}[/red]")
        return {"error": f"Failed to load configuration from: {config_file}"}

    # Validate pipeline setup
    rich_print("[yellow]🔧 Validating pipeline setup...[/yellow]")
    if not validate_pipeline_setup(config):
        rich_print("[red]❌ Pipeline setup validation failed[/red]")
        return {"error": "Pipeline setup validation failed"}

    # Process molecules with progress bar
    rich_print("[green]🚀 Starting batch processing...[/green]")

    successful_count = 0
    failed_count = 0

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("({task.completed}/{task.total})"),
        TimeElapsedColumn(),
    ) as progress:

        task = progress.add_task("Processing molecules...", total=len(identifiers))

        for identifier in identifiers:
            progress.update(task, description=f"Processing: {identifier[:30]}...")

            try:
                success = process_single_molecule(identifier, config)
                if success:
                    successful_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                failed_count += 1
                if verbose:
                    rich_print(f"[red]❌ Error processing {identifier}: {e}[/red]")

            progress.update(task, advance=1)

    # Display final results
    results_table = Table(title="Batch Processing Results")
    results_table.add_column("Metric", style="bold")
    results_table.add_column("Count", justify="right")
    results_table.add_column("Percentage", justify="right")

    total = len(identifiers)
    success_pct = (successful_count / total) * 100 if total > 0 else 0
    failed_pct = (failed_count / total) * 100 if total > 0 else 0

    results_table.add_row("Total Molecules", str(total), "100.0%")
    results_table.add_row(
        "Successfully Processed", str(successful_count), f"{success_pct:.1f}%",
        style="green"
    )
    results_table.add_row(
        "Failed", str(failed_count), f"{failed_pct:.1f}%", style="red"
    )

    console.print(results_table)

    if successful_count > 0:
        rich_print(
            f"[green]🎉 Batch processing completed! {successful_count} "
            f"molecules processed successfully.[/green]"
        )

    if failed_count > 0:
        rich_print(
            f"[yellow]⚠️  {failed_count} molecules failed processing. "
            f"Check logs for details.[/yellow]"
        )

    return {
        "total": total,
        "successful": successful_count,
        "failed": failed_count,
        "success_percentage": success_pct
    }


def _execute_info_logic(config_file: str) -> bool:
    """
    Execute system info display logic.

    Args:
        config_file: Path to configuration file

    Returns:
        bool: True if info was displayed successfully
    """
    console.print(Panel.fit(
        "[bold blue]🧪 Grimperium v2 - Diagnóstico do Sistema[/bold blue]",
        border_style="blue"
    ))

    # Create diagnostic table
    table = Table(title="Sistema e Dependências")
    table.add_column("Componente", style="bold", width=25)
    table.add_column("Status", justify="center", width=8)
    table.add_column("Detalhes / Versão", width=50)

    # System Information
    os_name = platform.system()
    os_version = platform.release()
    architecture = platform.machine()
    python_version = (
        f"{sys.version_info.major}.{sys.version_info.minor}."
        f"{sys.version_info.micro}"
    )

    table.add_row(
        "Sistema Operacional", "✅", f"{os_name} {os_version} ({architecture})"
    )
    table.add_row("Python", "✅", python_version)

    # Conda Environment
    conda_env = os.environ.get('CONDA_DEFAULT_ENV', 'N/A')
    if conda_env != 'N/A':
        table.add_row("Ambiente Conda", "✅", conda_env)
    else:
        table.add_row("Ambiente Conda", "⚠️", "Não detectado")

    # Add separator
    table.add_row("", "", "")

    # External Executables
    executables = ["crest", "mopac", "obabel"]

    for exe in executables:
        exe_path = shutil.which(exe)
        if exe_path:
            version_info = get_executable_version(exe)
            table.add_row(f"Executável: {exe}", "✅", f"{exe_path}")
            table.add_row("", "", f"Versão: {version_info}")
        else:
            table.add_row(f"Executável: {exe}", "❌", "Não encontrado no PATH")

    # Add separator
    table.add_row("", "", "")

    # Python Libraries
    libraries = ["pandas", "typer", "rich", "pydantic", "pyyaml", "requests"]

    for lib in libraries:
        version = get_library_version(lib)
        if version != "Not installed":
            table.add_row(f"Biblioteca: {lib}", "✅", version)
        else:
            table.add_row(f"Biblioteca: {lib}", "❌", "Não instalada")

    console.print(table)

    # Configuration Status
    console.print()
    config = load_config(config_file, PROJECT_ROOT)
    if config:
        console.print("[green]✅ Configuração carregada com sucesso[/green]")

        # Validate executables
        from grimperium.utils.config_manager import validate_executables
        if validate_executables(config):
            console.print(
                "[green]✅ Todos os executáveis necessários estão disponíveis[/green]"
            )
        else:
            console.print("[red]❌ Alguns executáveis necessários estão faltando[/red]")

        # Validate pipeline setup
        if validate_pipeline_setup(config):
            console.print("[green]✅ Configuração do pipeline é válida[/green]")
        else:
            console.print("[red]❌ Validação da configuração do pipeline falhou[/red]")

        # Overall system status
        console.print()
        missing_executables = [
            exe for exe in executables if not shutil.which(exe)
        ]
        missing_libraries = [
            lib for lib in libraries if get_library_version(lib) == "Not installed"
        ]

        if not missing_executables and not missing_libraries:
            console.print(
                "[green]🎉 Sistema configurado corretamente e pronto para "
                "execução![/green]"
            )
        else:
            console.print(
                "[yellow]⚠️  Sistema parcialmente configurado. Algumas "
                "dependências estão faltando.[/yellow]"
            )

            if missing_executables:
                console.print(
                    f"[red]   • Executáveis faltando: "
                    f"{', '.join(missing_executables)}[/red]"
                )
            if missing_libraries:
                console.print(
                    f"[red]   • Bibliotecas faltando: "
                    f"{', '.join(missing_libraries)}[/red]"
                )

        return True

    else:
        console.print(f"[red]❌ Falha ao carregar configuração de: {config_file}[/red]")
        return False


def _execute_report_logic(
    config_file: str, detailed: bool = False, missing: int = 0
) -> bool:
    """
    Execute progress report generation logic.

    Args:
        config_file: Path to configuration file
        detailed: Show detailed analysis
        missing: Number of missing molecules to show

    Returns:
        bool: True if report was generated successfully
    """
    console.print(Panel.fit(
        "[bold blue]🧪 Grimperium v2 - Progress Report[/bold blue]",
        border_style="blue"
    ))

    # Load configuration
    config = load_config(config_file, PROJECT_ROOT)
    if not config:
        rich_print(f"[red]❌ Failed to load configuration from: {config_file}[/red]")
        return False

    # Get database paths from configuration
    cbs_db_path = config['database']['cbs_db_path']
    pm7_db_path = config['database']['pm7_db_path']

    # Generate progress report
    rich_print("[yellow]📊 Analyzing database progress...[/yellow]")
    report_data = generate_progress_report(cbs_db_path, pm7_db_path)

    # Check for errors
    if 'error' in report_data:
        rich_print(f"[red]❌ Error generating report: {report_data['error']}[/red]")
        return False

    # Create main progress panel
    progress_content = []

    # Database status
    cbs_status = "✅ Found" if report_data['cbs_exists'] else "❌ Missing"
    pm7_status = "✅ Found" if report_data['pm7_exists'] else "❌ Missing"

    progress_content.append("[bold]Database Status:[/bold]")
    progress_content.append(f"  CBS Reference Database: {cbs_status}")
    progress_content.append(f"  PM7 Calculated Database: {pm7_status}")
    progress_content.append("")

    # Main metrics
    progress_content.append("[bold]Calculation Progress:[/bold]")
    progress_content.append(
        f"  Molecules in Reference Database: [cyan]{report_data['total_cbs']:,}[/cyan]"
    )
    progress_content.append(
        f"  Molecules Calculated with PM7: [green]{report_data['total_pm7']:,}[/green]"
    )
    progress_content.append(
        f"  Molecules in Common: [blue]{report_data['common_count']:,}[/blue]"
    )
    progress_content.append("")

    # Progress percentage with color coding
    progress_pct = report_data['progress_percentage']
    if progress_pct >= 90:
        progress_color = "green"
        progress_emoji = "🎉"
    elif progress_pct >= 75:
        progress_color = "blue"
        progress_emoji = "🚀"
    elif progress_pct >= 50:
        progress_color = "yellow"
        progress_emoji = "⚡"
    elif progress_pct >= 25:
        progress_color = "orange"
        progress_emoji = "🔥"
    else:
        progress_color = "red"
        progress_emoji = "🎯"

    progress_content.append("[bold]Overall Progress:[/bold]")
    progress_content.append(
        f"  {progress_emoji} [{progress_color}]{progress_pct:.2f}%"
        f"[/{progress_color}] Complete"
    )

    # Additional insights
    if report_data['missing_count'] > 0:
        progress_content.append(
            f"  Remaining to Calculate: [red]{report_data['missing_count']:,}[/red]"
        )

    if report_data['extra_count'] > 0:
        progress_content.append(
            f"  Extra Calculations: [yellow]{report_data['extra_count']:,}[/yellow]"
        )

    # Display main progress panel
    console.print(Panel(
        "\n".join(progress_content),
        title="[bold blue]Grimperium Progress Report[/bold blue]",
        border_style="blue",
        padding=(1, 2)
    ))

    # Show detailed analysis if requested
    if detailed:
        rich_print("\n[yellow]📋 Detailed Database Analysis...[/yellow]")

        # Analyze CBS database
        cbs_analysis = get_detailed_database_analysis(cbs_db_path)
        pm7_analysis = get_detailed_database_analysis(pm7_db_path)

        # Create detailed table
        detail_table = Table(title="Detailed Database Analysis")
        detail_table.add_column("Database", style="bold")
        detail_table.add_column("Status", justify="center")
        detail_table.add_column("Entries", justify="right")
        detail_table.add_column("Unique SMILES", justify="right")
        detail_table.add_column("File Size", justify="right")
        detail_table.add_column("Data Quality", justify="center")

        # CBS row
        if cbs_analysis['exists']:
            detail_table.add_row(
                "CBS Reference",
                "[green]✅ Active[/green]",
                f"{cbs_analysis['total_entries']:,}",
                f"{cbs_analysis['unique_smiles']:,}",
                f"{cbs_analysis['file_size_mb']:.1f} MB",
                f"[green]{cbs_analysis['data_quality']}[/green]"
            )
        else:
            detail_table.add_row(
                "CBS Reference",
                "[red]❌ Missing[/red]",
                "0",
                "0",
                "0 MB",
                "[red]N/A[/red]"
            )

        # PM7 row
        if pm7_analysis['exists']:
            detail_table.add_row(
                "PM7 Calculated",
                "[green]✅ Active[/green]",
                f"{pm7_analysis['total_entries']:,}",
                f"{pm7_analysis['unique_smiles']:,}",
                f"{pm7_analysis['file_size_mb']:.1f} MB",
                f"[green]{pm7_analysis['data_quality']}[/green]"
            )
        else:
            detail_table.add_row(
                "PM7 Calculated",
                "[yellow]⚠️  Empty[/yellow]",
                "0",
                "0",
                "0 MB",
                "[yellow]Empty[/yellow]"
            )

        console.print(detail_table)

    # Show missing molecules if requested
    if missing > 0:
        rich_print(
            f"\n[yellow]🔍 Finding {missing} molecules that need "
            "calculation...[/yellow]"
        )
        missing_molecules = find_missing_molecules(cbs_db_path, pm7_db_path, missing)

        if missing_molecules:
            missing_table = Table(
                title=f"Next {len(missing_molecules)} Molecules to Calculate"
            )
            missing_table.add_column("#", justify="right", style="dim")
            missing_table.add_column("SMILES", style="cyan")

            for i, smiles in enumerate(missing_molecules, 1):
                missing_table.add_row(str(i), smiles)

            console.print(missing_table)
        else:
            rich_print(
                "[green]🎉 No missing molecules found! All calculations are "
                "complete.[/green]"
            )

    # Success message
    if progress_pct == 100:
        rich_print(
            "\n[green]🎉 Congratulations! All reference molecules have been "
            "calculated![/green]"
        )
    elif progress_pct > 0:
        rich_print(
            f"\n[blue]📈 Keep up the great work! "
            f"{report_data['missing_count']:,} molecules remaining.[/blue]"
        )
    else:
        rich_print(
            f"\n[yellow]🚀 Ready to start calculations! "
            f"{report_data['total_cbs']:,} molecules await processing.[/yellow]"
        )

    return True


@app.command()
def run_single(
    config_file: str = typer.Option(
        "config.yaml",
        "--config",
        "-c",
        help="Path to configuration file"
    ),
    name: Optional[str] = typer.Option(
        None,
        "--name",
        "-n",
        help="Molecule name to search in PubChem"
    ),
    smiles: Optional[str] = typer.Option(
        None,
        "--smiles",
        "-s",
        help="SMILES string of the molecule"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output"
    )
) -> None:
    """
    Process a single molecule through the computational chemistry pipeline.

    This command runs the complete Grimperium workflow for a single molecule,
    from structure retrieval through energy calculation and database storage.

    You must specify either --name or --smiles (but not both).
    """
    # Validate input arguments
    if not name and not smiles:
        rich_print(
            "[red]❌ Error: You must specify either --name or --smiles[/red]"
        )
        raise typer.Exit(1)

    if name and smiles:
        rich_print("[red]❌ Error: You cannot specify both --name and --smiles[/red]")
        raise typer.Exit(1)

    # Use the provided identifier
    identifier = name if name else smiles
    identifier_type = "name" if name else "SMILES"

    # Ensure identifier is not None (should not happen due to validation above)
    if identifier is None:
        rich_print("[red]❌ Error: No identifier provided[/red]")
        raise typer.Exit(1)

    # Call the business logic function
    success = _execute_single_molecule_logic(
        identifier, identifier_type, config_file, verbose
    )

    if not success:
        raise typer.Exit(1)


@app.command()
def run_batch(
    file: str = typer.Argument(
        ...,
        help="Path to text file containing molecule identifiers (one per line)"
    ),
    config_file: str = typer.Option(
        "config.yaml",
        "--config",
        "-c",
        help="Path to configuration file"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output"
    )
) -> None:
    """
    Process multiple molecules from a file through the computational chemistry pipeline.

    This command reads molecule identifiers from a text file (one per line) and
    processes each through the complete Grimperium workflow. Progress is displayed
    with a progress bar.
    """
    # Call the business logic function
    result = _execute_batch_logic(file, config_file, verbose)

    if "error" in result:
        raise typer.Exit(1)


@app.command()
def report(
    config_file: str = typer.Option(
        "config.yaml",
        "--config",
        "-c",
        help="Path to configuration file"
    ),
    detailed: bool = typer.Option(
        False,
        "--detailed",
        "-d",
        help="Show detailed database analysis"
    ),
    missing: int = typer.Option(
        0,
        "--missing",
        "-m",
        help="Show N missing molecules that need calculation"
    )
) -> None:
    """
    Generate comprehensive progress report comparing CBS reference and
    PM7 calculated databases.

    This command analyzes the computational chemistry calculation progress by
    comparing the CBS reference database with the PM7 calculated results,
    providing insights into completion status and remaining work.
    """
    # Call the business logic function
    success = _execute_report_logic(config_file, detailed, missing)

    if not success:
        raise typer.Exit(1)


def get_executable_version(executable_name: str) -> str:
    """Get version information for an executable."""
    try:
        if executable_name == "crest":
            result = subprocess.run(
                [executable_name, "--version"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                # Extract version from output (format may vary)
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'version' in line.lower() or 'crest' in line.lower():
                        return line.strip()
                return "Version info available"
            return "Version unavailable"

        elif executable_name == "obabel":
            result = subprocess.run(
                [executable_name, "--version"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'open babel' in line.lower() or 'version' in line.lower():
                        return line.strip()
                return "Version info available"
            return "Version unavailable"

        elif executable_name == "mopac":
            result = subprocess.run(
                [executable_name],
                capture_output=True, text=True, timeout=10
            )
            # MOPAC might return version info in stderr or stdout
            output = result.stdout + result.stderr
            lines = output.strip().split('\n')
            for line in lines:
                if 'mopac' in line.lower() or 'version' in line.lower():
                    return line.strip()
            return "MOPAC detected"

        else:
            return "Version check not implemented"

    except subprocess.TimeoutExpired:
        return "Timeout getting version"
    except FileNotFoundError:
        return "Executable not found"
    except Exception as e:
        return f"Error: {str(e)}"


def get_library_version(library_name: str) -> str:
    """Get version of a Python library."""
    try:
        if library_name == "pandas":
            import pandas
            return pandas.__version__
        elif library_name == "typer":
            import typer
            return typer.__version__
        elif library_name == "rich":
            import rich
            return getattr(rich, '__version__', 'Version unavailable')
        elif library_name == "pydantic":
            import pydantic
            return pydantic.__version__
        elif library_name == "pyyaml":
            import yaml
            return yaml.__version__
        elif library_name == "requests":
            import requests
            return requests.__version__
        else:
            return "Unknown library"
    except ImportError:
        return "Not installed"
    except AttributeError:
        return "Version unavailable"
    except Exception as e:
        return f"Error: {str(e)}"


@app.command()
def info(
    config_file: str = typer.Option(
        "config.yaml",
        "--config",
        "-c",
        help="Path to configuration file"
    )
) -> None:
    """
    Display comprehensive system information and diagnostic report.
    """
    # Call the business logic function
    success = _execute_info_logic(config_file)

    if not success:
        raise typer.Exit(1)


def interactive_menu():
    """
    Interactive menu for Grimperium using questionary.
    """
    console.print(Panel.fit(
        "[bold blue]🧪 Grimperium v2 - Menu Interativo[/bold blue]\n"
        "[cyan]Computational Chemistry Workflow Automation[/cyan]",
        border_style="blue"
    ))

    while True:
        try:
            choice = questionary.select(
                "O que você gostaria de fazer?",
                choices=[
                    "Processar uma única molécula",
                    "Processar um lote de moléculas de um arquivo",
                    "Verificar o status do sistema",
                    "Gerar um relatório de progresso",
                    "Sair"
                ],
                style=questionary.Style([
                    ('question', 'bold'),
                    ('answer', 'fg:#ff9d00 bold'),
                    ('pointer', 'fg:#ff9d00 bold'),
                    ('highlighted', 'fg:#ff9d00 bold'),
                    ('selected', 'fg:#cc5454'),
                    ('separator', 'fg:#cc5454'),
                    ('instruction', ''),
                    ('text', ''),
                    ('disabled', 'fg:#858585 italic')
                ])
            ).ask()

            if choice == "Processar uma única molécula":
                handle_single_molecule()
            elif choice == "Processar um lote de moléculas de um arquivo":
                handle_batch_molecules()
            elif choice == "Verificar o status do sistema":
                handle_system_info()
            elif choice == "Gerar um relatório de progresso":
                handle_progress_report()
            elif choice == "Sair":
                rich_print("[cyan]👋 Obrigado por usar o Grimperium![/cyan]")
                break
            else:
                rich_print("[red]❌ Opção inválida[/red]")

        except KeyboardInterrupt:
            rich_print("\n[cyan]👋 Operação cancelada. Até logo![/cyan]")
            break
        except Exception as e:
            rich_print(f"[red]❌ Erro inesperado: {e}[/red]")
            break


def handle_single_molecule():
    """
    Handle single molecule processing through interactive prompts.
    """
    console.print(Panel.fit(
        "[bold green]🧪 Processar Uma Única Molécula[/bold green]",
        border_style="green"
    ))

    # Ask for input type
    input_type = questionary.select(
        "Qual o tipo de entrada?",
        choices=["Nome Químico", "SMILES"]
    ).ask()

    if input_type == "Nome Químico":
        molecule_input = questionary.text(
            "Por favor, digite o Nome Químico:",
            validate=lambda text: (
                len(text.strip()) > 0 or "O nome não pode estar vazio"
            )
        ).ask()

        if molecule_input:
            try:
                _execute_single_molecule_logic(
                    identifier=molecule_input.strip(),
                    identifier_type="name",
                    config_file='config.yaml',
                    verbose=False
                )
            except Exception as e:
                rich_print(f"[red]❌ Erro no processamento: {e}[/red]")

    elif input_type == "SMILES":
        molecule_input = questionary.text(
            "Por favor, digite o SMILES:",
            validate=lambda text: (
                len(text.strip()) > 0 or "O SMILES não pode estar vazio"
            )
        ).ask()

        if molecule_input:
            try:
                _execute_single_molecule_logic(
                    identifier=molecule_input.strip(),
                    identifier_type="SMILES",
                    config_file='config.yaml',
                    verbose=False
                )
            except Exception as e:
                rich_print(f"[red]❌ Erro no processamento: {e}[/red]")

    # Pause before returning to menu
    questionary.press_any_key_to_continue(
        "Pressione qualquer tecla para continuar..."
    ).ask()


def handle_batch_molecules():
    """
    Handle batch molecule processing through interactive prompts.
    """
    console.print(Panel.fit(
        "[bold green]📁 Processar Lote de Moléculas[/bold green]",
        border_style="green"
    ))

    # Ask for file path
    file_path = questionary.path(
        "Selecione o arquivo com as moléculas (um identificador por linha):",
        validate=lambda path: Path(path).exists() or "Arquivo não encontrado"
    ).ask()

    if file_path:
        try:
            result = _execute_batch_logic(
                file_path=file_path,
                config_file='config.yaml',
                verbose=False
            )
            if "error" in result:
                rich_print(
                    f"[red]❌ Erro no processamento do lote: {result['error']}[/red]"
                )
        except Exception as e:
            rich_print(f"[red]❌ Erro no processamento do lote: {e}[/red]")

    # Pause before returning to menu
    questionary.press_any_key_to_continue(
        "Pressione qualquer tecla para continuar..."
    ).ask()


def handle_system_info():
    """
    Handle system information display.
    """
    try:
        _execute_info_logic(config_file='config.yaml')
    except Exception as e:
        rich_print(f"[red]❌ Erro ao obter informações do sistema: {e}[/red]")

    # Pause before returning to menu
    questionary.press_any_key_to_continue(
        "Pressione qualquer tecla para continuar..."
    ).ask()


def handle_progress_report():
    """
    Handle progress report generation.
    """
    console.print(Panel.fit(
        "[bold green]📊 Relatório de Progresso[/bold green]",
        border_style="green"
    ))

    # Ask for report options
    detailed = questionary.confirm(
        "Deseja um relatório detalhado?",
        default=False
    ).ask()

    missing_count = 0
    if questionary.confirm(
        "Deseja ver moléculas que precisam ser calculadas?",
        default=False
    ).ask():
        missing_count = questionary.text(
            "Quantas moléculas mostrar?",
            default="10",
            validate=lambda text: (
                text.isdigit() and int(text) > 0 or
                "Digite um número válido maior que 0"
            )
        ).ask()
        missing_count = int(missing_count) if missing_count else 0

    try:
        _execute_report_logic(
            config_file='config.yaml',
            detailed=detailed,
            missing=missing_count
        )
    except Exception as e:
        rich_print(f"[red]❌ Erro ao gerar relatório: {e}[/red]")

    # Pause before returning to menu
    questionary.press_any_key_to_continue(
        "Pressione qualquer tecla para continuar..."
    ).ask()


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        help="Show version information"
    )
):
    """
    Grimperium v2 - Computational Chemistry Workflow Automation Tool

    Run without arguments to start the interactive menu.
    """
    if version:
        rich_print(
            "[bold blue]Grimperium v2[/bold blue] - "
            "Computational Chemistry Workflow Automation Tool"
        )
        return

    # If no subcommand was invoked, start interactive menu
    if ctx.invoked_subcommand is None:
        interactive_menu()


if __name__ == "__main__":
    app()
