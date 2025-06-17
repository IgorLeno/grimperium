#!/usr/bin/env python3
"""
Grimperium v2 - Computational Chemistry Workflow Automation Tool

This is the main entry point for the Grimperium application, which provides
automated workflows for computational chemistry calculations including 
conformational search, quantum chemical calculations, and thermodynamic analysis.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import typer
from rich import print as rich_print
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.table import Table

from grimperium.utils.config_manager import load_config
from grimperium.services.pipeline_orchestrator import (
    process_single_molecule,
    process_molecule_batch,
    validate_pipeline_setup
)
from grimperium.services.analysis_service import (
    generate_progress_report,
    get_detailed_database_analysis,
    find_missing_molecules
)

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
    setup_logging(verbose)
    
    # Validate input arguments
    if not name and not smiles:
        rich_print("[red]❌ Error: You must specify either --name or --smiles[/red]")
        raise typer.Exit(1)
        
    if name and smiles:
        rich_print("[red]❌ Error: You cannot specify both --name and --smiles[/red]")
        raise typer.Exit(1)
    
    # Use the provided identifier
    identifier = name if name else smiles
    identifier_type = "name" if name else "SMILES"
    
    # Display welcome message
    console.print(Panel.fit(
        "[bold blue]🧪 Grimperium v2[/bold blue]\n"
        "[cyan]Computational Chemistry Workflow Automation[/cyan]",
        border_style="blue"
    ))
    
    # Load configuration
    rich_print(f"[yellow]📋 Loading configuration from: {config_file}[/yellow]")
    config = load_config(config_file)
    if not config:
        rich_print(f"[red]❌ Failed to load configuration from: {config_file}[/red]")
        raise typer.Exit(1)
    
    # Validate pipeline setup
    rich_print("[yellow]🔧 Validating pipeline setup...[/yellow]")
    if not validate_pipeline_setup(config):
        rich_print("[red]❌ Pipeline setup validation failed[/red]")
        raise typer.Exit(1)
    
    # Process the molecule
    rich_print(f"[green]🚀 Processing molecule ({identifier_type}): {identifier}[/green]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("Processing molecule...", total=None)
        success = process_single_molecule(identifier, config)
    
    # Display results
    if success:
        rich_print(f"[green]✅ Successfully processed: {identifier}[/green]")
        rich_print("[green]🎉 Results saved to database![/green]")
    else:
        rich_print(f"[red]❌ Failed to process: {identifier}[/red]")
        rich_print("[red]💥 Check the logs for detailed error information[/red]")
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
    setup_logging(verbose)
    
    # Display welcome message
    console.print(Panel.fit(
        "[bold blue]🧪 Grimperium v2 - Batch Mode[/bold blue]\n"
        "[cyan]Computational Chemistry Workflow Automation[/cyan]",
        border_style="blue"
    ))
    
    # Validate input file
    input_file = Path(file)
    if not input_file.exists():
        rich_print(f"[red]❌ Input file not found: {file}[/red]")
        raise typer.Exit(1)
    
    # Load molecule identifiers
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            identifiers = [line.strip() for line in f if line.strip()]
    except Exception as e:
        rich_print(f"[red]❌ Error reading input file: {e}[/red]")
        raise typer.Exit(1)
    
    if not identifiers:
        rich_print(f"[red]❌ No molecule identifiers found in: {file}[/red]")
        raise typer.Exit(1)
    
    rich_print(f"[green]📄 Loaded {len(identifiers)} molecule identifiers[/green]")
    
    # Load configuration
    rich_print(f"[yellow]📋 Loading configuration from: {config_file}[/yellow]")
    config = load_config(config_file)
    if not config:
        rich_print(f"[red]❌ Failed to load configuration from: {config_file}[/red]")
        raise typer.Exit(1)
    
    # Validate pipeline setup
    rich_print("[yellow]🔧 Validating pipeline setup...[/yellow]")
    if not validate_pipeline_setup(config):
        rich_print("[red]❌ Pipeline setup validation failed[/red]")
        raise typer.Exit(1)
    
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
        
        for i, identifier in enumerate(identifiers):
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
    results_table.add_row("Successfully Processed", str(successful_count), f"{success_pct:.1f}%", style="green")
    results_table.add_row("Failed", str(failed_count), f"{failed_pct:.1f}%", style="red")
    
    console.print(results_table)
    
    if successful_count > 0:
        rich_print(f"[green]🎉 Batch processing completed! {successful_count} molecules processed successfully.[/green]")
    
    if failed_count > 0:
        rich_print(f"[yellow]⚠️  {failed_count} molecules failed processing. Check logs for details.[/yellow]")


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
    Generate comprehensive progress report comparing CBS reference and PM7 calculated databases.
    
    This command analyzes the computational chemistry calculation progress by comparing
    the CBS reference database with the PM7 calculated results, providing insights
    into completion status and remaining work.
    """
    console.print(Panel.fit(
        "[bold blue]🧪 Grimperium v2 - Progress Report[/bold blue]",
        border_style="blue"
    ))
    
    # Load configuration
    config = load_config(config_file)
    if not config:
        rich_print(f"[red]❌ Failed to load configuration from: {config_file}[/red]")
        raise typer.Exit(1)
    
    # Get database paths from configuration
    cbs_db_path = config['database']['cbs_db_path']
    pm7_db_path = config['database']['pm7_db_path']
    
    # Generate progress report
    rich_print("[yellow]📊 Analyzing database progress...[/yellow]")
    report_data = generate_progress_report(cbs_db_path, pm7_db_path)
    
    # Check for errors
    if 'error' in report_data:
        rich_print(f"[red]❌ Error generating report: {report_data['error']}[/red]")
        raise typer.Exit(1)
    
    # Create main progress panel
    progress_content = []
    
    # Database status
    cbs_status = "✅ Found" if report_data['cbs_exists'] else "❌ Missing"
    pm7_status = "✅ Found" if report_data['pm7_exists'] else "❌ Missing"
    
    progress_content.append(f"[bold]Database Status:[/bold]")
    progress_content.append(f"  CBS Reference Database: {cbs_status}")
    progress_content.append(f"  PM7 Calculated Database: {pm7_status}")
    progress_content.append("")
    
    # Main metrics
    progress_content.append(f"[bold]Calculation Progress:[/bold]")
    progress_content.append(f"  Molecules in Reference Database: [cyan]{report_data['total_cbs']:,}[/cyan]")
    progress_content.append(f"  Molecules Calculated with PM7: [green]{report_data['total_pm7']:,}[/green]")
    progress_content.append(f"  Molecules in Common: [blue]{report_data['common_count']:,}[/blue]")
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
    
    progress_content.append(f"[bold]Overall Progress:[/bold]")
    progress_content.append(f"  {progress_emoji} [{progress_color}]{progress_pct:.2f}%[/{progress_color}] Complete")
    
    # Additional insights
    if report_data['missing_count'] > 0:
        progress_content.append(f"  Remaining to Calculate: [red]{report_data['missing_count']:,}[/red]")
    
    if report_data['extra_count'] > 0:
        progress_content.append(f"  Extra Calculations: [yellow]{report_data['extra_count']:,}[/yellow]")
    
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
        rich_print(f"\n[yellow]🔍 Finding {missing} molecules that need calculation...[/yellow]")
        missing_molecules = find_missing_molecules(cbs_db_path, pm7_db_path, missing)
        
        if missing_molecules:
            missing_table = Table(title=f"Next {len(missing_molecules)} Molecules to Calculate")
            missing_table.add_column("#", justify="right", style="dim")
            missing_table.add_column("SMILES", style="cyan")
            
            for i, smiles in enumerate(missing_molecules, 1):
                missing_table.add_row(str(i), smiles)
            
            console.print(missing_table)
        else:
            rich_print("[green]🎉 No missing molecules found! All calculations are complete.[/green]")
    
    # Success message
    if progress_pct == 100:
        rich_print("\n[green]🎉 Congratulations! All reference molecules have been calculated![/green]")
    elif progress_pct > 0:
        rich_print(f"\n[blue]📈 Keep up the great work! {report_data['missing_count']:,} molecules remaining.[/blue]")
    else:
        rich_print(f"\n[yellow]🚀 Ready to start calculations! {report_data['total_cbs']:,} molecules await processing.[/yellow]")


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
    Display system information and configuration status.
    """
    console.print(Panel.fit(
        "[bold blue]🧪 Grimperium v2 - System Information[/bold blue]",
        border_style="blue"
    ))
    
    # Load and display configuration
    config = load_config(config_file)
    if config:
        rich_print("[green]✅ Configuration loaded successfully[/green]")
        
        # Validate executables
        from grimperium.utils.config_manager import validate_executables
        if validate_executables(config):
            rich_print("[green]✅ All required executables are available[/green]")
        else:
            rich_print("[red]❌ Some required executables are missing[/red]")
        
        # Validate pipeline setup
        if validate_pipeline_setup(config):
            rich_print("[green]✅ Pipeline setup is valid[/green]")
        else:
            rich_print("[red]❌ Pipeline setup validation failed[/red]")
    else:
        rich_print(f"[red]❌ Failed to load configuration from: {config_file}[/red]")


if __name__ == "__main__":
    app()