"""
Interactive batch workflow for Grimperium molecule list management.

This module provides a guided, error-proof interface for creating and
validating molecule lists using rich and questionary libraries.
"""

import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any

import questionary
from rich import print as rich_print
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ..services import database_service
from ..services.pipeline_orchestrator import (
    process_single_molecule,
    get_molecule_smiles,
)


class InteractiveBatchWorkflow:
    """
    Interactive workflow for batch molecule processing.

    Provides a guided interface for creating, editing, and validating
    molecule lists before batch processing.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the interactive batch workflow.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.console = Console()
        self.logger = logging.getLogger(__name__)

        # Extract paths from config
        self.lists_dir = Path(config["general_settings"]["lists_directory"])
        self.repo_base = Path(config["repository_base_path"])
        self.not_found_dir = self.repo_base / "not-found"
        self.pm7_db_path = config["database"]["pm7_db_path"]

        # Current molecule list
        self.molecules: List[str] = []
        self.current_file: Optional[str] = None

        # SMILES mapping (populated during validation)
        self.molecule_smiles_map: Dict[str, str] = {}

        # Overwrite tracking (molecules user chose to overwrite)
        self.molecules_to_overwrite: set = set()

        # Validation state tracking
        self._validation_completed = False

    def run(self) -> bool:
        """
        Run the interactive batch workflow.

        Returns:
            True if batch processing was started, False if cancelled
        """
        self.console.print(
            Panel.fit(
                (
                    "[bold blue]🧪 Grimperium v2 - Gerenciador Interativo de Lotes"
                    "[/bold blue]\n"
                    "[cyan]Criação e validação guiada de listas de moléculas[/cyan]"
                ),
                border_style="blue",
            )
        )

        try:
            # Main menu
            if not self._show_main_menu():
                return False

            # Interactive editing mode
            if not self._interactive_editing_mode():
                return False

            # Validation steps
            if not self._validation_steps():
                return False

            # Save final list and start processing
            return self._start_batch_processing()

        except KeyboardInterrupt:
            rich_print("\n[yellow]⚠️  Operação cancelada pelo usuário[/yellow]")
            return False
        except Exception as e:
            self.logger.error(f"Error in interactive batch workflow: {e}")
            rich_print(f"[red]❌ Erro inesperado: {e}[/red]")
            return False

    def _show_main_menu(self) -> bool:
        """
        Show the main menu and handle user choice.

        Returns:
            True to continue, False to exit
        """
        choice = questionary.select(
            "Como você gostaria de proceder?",
            choices=[
                "Iniciar uma lista do zero",
                "Carregar uma lista para editar",
                "Sair",
            ],
            style=questionary.Style(
                [
                    ("question", "bold"),
                    ("answer", "fg:#ff9d00 bold"),
                    ("pointer", "fg:#ff9d00 bold"),
                    ("highlighted", "fg:#ff9d00 bold"),
                    ("selected", "fg:#cc5454"),
                ]
            ),
        ).ask()

        if choice == "Iniciar uma lista do zero":
            self.molecules = []
            self.current_file = None
            return True
        elif choice == "Carregar uma lista para editar":
            return self._load_existing_list()
        else:
            rich_print("[cyan]👋 Até logo![/cyan]")
            return False

    def _load_existing_list(self) -> bool:
        """
        Load an existing list from the lists directory.

        Returns:
            True if list was loaded, False to return to main menu
        """
        # Get all .txt files in the lists directory
        txt_files = list(self.lists_dir.glob("*.txt"))

        if not txt_files:
            rich_print(
                f"[yellow]ℹ️  Nenhuma lista encontrada no diretório "
                f"{self.lists_dir}[/yellow]"
            )
            rich_print(
                "[yellow]   Redirecionando para criação de nova lista...[/yellow]"
            )
            self.molecules = []
            self.current_file = None
            return True

        # Create choices with just filenames
        file_choices = [f.name for f in txt_files]
        file_choices.append("← Voltar ao menu principal")

        choice = questionary.select(
            f"Selecione a lista para editar (encontradas {len(txt_files)} listas):",
            choices=file_choices,
        ).ask()

        if choice == "← Voltar ao menu principal":
            return self._show_main_menu()

        # Load the selected file
        selected_file = self.lists_dir / choice
        try:
            with open(selected_file, "r", encoding="utf-8") as f:
                self.molecules = [line.strip() for line in f if line.strip()]

            self.current_file = choice
            rich_print(
                f"[green]✅ Lista carregada: {choice} "
                f"({len(self.molecules)} moléculas)[/green]"
            )
            return True

        except Exception as e:
            self.logger.error(f"Error loading list {selected_file}: {e}")
            rich_print(f"[red]❌ Erro ao carregar a lista: {e}[/red]")
            return self._show_main_menu()

    def _interactive_editing_mode(self) -> bool:
        """
        Interactive editing mode for the molecule list.

        Returns:
            True to continue to validation, False to cancel
        """
        while True:
            # Display current list
            self._display_molecule_table()

            # Show action menu
            action = questionary.select(
                "Escolha uma ação:",
                choices=[
                    "(a) Adicionar molécula única",
                    "(l) Adicionar de outra lista",
                    "(e) Editar molécula",
                    "(r) Remover molécula",
                    "(c) Confirmar lista e continuar",
                    "(s) Sair sem salvar",
                ],
            ).ask()

            if action.startswith("(a)"):
                self._add_single_molecule()
                # Reset validation state after adding
                self._reset_validation_state()
            elif action.startswith("(l)"):
                self._add_from_another_list()
                # Validation reset is handled inside _add_from_another_list
            elif action.startswith("(e)"):
                self._edit_molecule()
                # Reset validation state after editing
                self._reset_validation_state()
            elif action.startswith("(r)"):
                self._remove_molecule()
                # Reset validation state after removing
                self._reset_validation_state()
            elif action.startswith("(c)"):
                if len(self.molecules) == 0:
                    rich_print(
                        "[yellow]⚠️  A lista está vazia. Adicione pelo menos uma "
                        "molécula.[/yellow]"
                    )
                    continue
                return True
            elif action.startswith("(s)"):
                if questionary.confirm("Tem certeza que deseja sair sem salvar?").ask():
                    return False

    def _display_molecule_table(self) -> None:
        """Display the current molecule list in a rich table."""
        table = Table(title=f"Lista Atual de Moléculas ({len(self.molecules)} itens)")
        table.add_column("#", justify="right", style="cyan", width=4)
        table.add_column("Molécula", style="white")

        if not self.molecules:
            table.add_row("—", "[dim]Lista vazia[/dim]")
        else:
            for i, molecule in enumerate(self.molecules, 1):
                table.add_row(str(i), molecule)

        self.console.print()
        self.console.print(table)
        self.console.print()

    def _add_single_molecule(self) -> None:
        """Add a single molecule to the list."""
        molecule = questionary.text(
            "Digite o nome da molécula:",
            validate=lambda text: len(text.strip()) > 0
            or "O nome não pode estar vazio",
        ).ask()

        if molecule:
            molecule = molecule.strip()
            if molecule in self.molecules:
                rich_print(
                    f"[yellow]⚠️  A molécula '{molecule}' já existe na lista[/yellow]"
                )
            else:
                self.molecules.append(molecule)
                rich_print(f"[green]✅ Molécula '{molecule}' adicionada[/green]")

    def _add_from_another_list(self) -> None:
        """Add molecules from another list file."""
        # Get all .txt files except the current one
        txt_files = [
            f
            for f in self.lists_dir.glob("*.txt")
            if self.current_file is None or f.name != self.current_file
        ]

        if not txt_files:
            rich_print("[yellow]ℹ️  Nenhuma outra lista encontrada[/yellow]")
            return

        file_choices = [f.name for f in txt_files]
        file_choices.append("← Cancelar")

        choice = questionary.select(
            "Selecione a lista para importar:", choices=file_choices
        ).ask()

        if choice == "← Cancelar":
            return

        # Load and add molecules
        selected_file = self.lists_dir / choice
        try:
            with open(selected_file, "r", encoding="utf-8") as f:
                new_molecules = [line.strip() for line in f if line.strip()]

            added_count = 0
            duplicate_count = 0

            for molecule in new_molecules:
                if molecule not in self.molecules:
                    self.molecules.append(molecule)
                    added_count += 1
                else:
                    duplicate_count += 1

            rich_print(
                f"[green]✅ {added_count} moléculas adicionadas de {choice}[/green]"
            )
            if duplicate_count > 0:
                rich_print(
                    f"[yellow]ℹ️  {duplicate_count} moléculas duplicadas "
                    f"ignoradas[/yellow]"
                )

            # Clear previous validation state since list has changed
            self._reset_validation_state()
            rich_print(
                "[blue]ℹ️  Lista modificada - validação será executada novamente[/blue]"
            )

        except Exception as e:
            self.logger.error(f"Error loading list {selected_file}: {e}")
            rich_print(f"[red]❌ Erro ao carregar a lista: {e}[/red]")

    def _edit_molecule(self) -> None:
        """Edit a molecule in the list."""
        if not self.molecules:
            rich_print("[yellow]ℹ️  Lista vazia - nada para editar[/yellow]")
            return

        line_num = questionary.text(
            f"Digite o número da linha para editar (1-{len(self.molecules)}):",
            validate=lambda text: (
                text.isdigit() and 1 <= int(text) <= len(self.molecules)
            )
            or f"Digite um número entre 1 e {len(self.molecules)}",
        ).ask()

        if line_num:
            index = int(line_num) - 1
            current_molecule = self.molecules[index]

            new_molecule = questionary.text(
                f"Editar molécula (atual: {current_molecule}):",
                default=current_molecule,
                validate=lambda text: len(text.strip()) > 0
                or "O nome não pode estar vazio",
            ).ask()

            if new_molecule and new_molecule.strip() != current_molecule:
                new_molecule = new_molecule.strip()
                if new_molecule in self.molecules:
                    rich_print(
                        f"[yellow]⚠️  A molécula '{new_molecule}' já existe na "
                        f"lista[/yellow]"
                    )
                else:
                    self.molecules[index] = new_molecule
                    rich_print(
                        f"[green]✅ Molécula editada: {current_molecule} → "
                        f"{new_molecule}[/green]"
                    )

    def _remove_molecule(self) -> None:
        """Remove a molecule from the list."""
        if not self.molecules:
            rich_print("[yellow]ℹ️  Lista vazia - nada para remover[/yellow]")
            return

        line_num = questionary.text(
            f"Digite o número da linha para remover (1-{len(self.molecules)}):",
            validate=lambda text: (
                text.isdigit() and 1 <= int(text) <= len(self.molecules)
            )
            or f"Digite um número entre 1 e {len(self.molecules)}",
        ).ask()

        if line_num:
            index = int(line_num) - 1
            removed_molecule = self.molecules.pop(index)
            rich_print(f"[green]✅ Molécula '{removed_molecule}' removida[/green]")

    def _validation_steps(self) -> bool:
        """
        Perform validation steps on the final list.

        This method ensures three sequential validation steps:
        1. SMILES conversion (pre-processing)
        2. Database duplicate check
        3. PubChem availability check

        Returns:
            True to continue processing, False to cancel or return to editing
        """
        rich_print("\n[yellow]🔍 Iniciando validação da lista...[/yellow]")

        # Step 1: SMILES conversion (pre-processing)
        if not self._convert_molecules_to_smiles():
            return False

        # Step 2: Database duplicate validation
        if not self._validate_database_duplicates():
            return False

        # Step 3: PubChem availability validation
        return self._validate_pubchem_availability()

    def _convert_molecules_to_smiles(self) -> bool:
        """
        Convert all molecule names to SMILES strings.

        This is the first validation step that must complete successfully
        before proceeding to database duplicate checking.

        Returns:
            True to continue to next validation step, False to return to editing
        """
        rich_print("[yellow]🔍 Convertendo nomes das moléculas para SMILES...[/yellow]")

        try:
            # Clear previous SMILES mapping and overwrite tracking
            self.molecule_smiles_map = {}
            self.molecules_to_overwrite = set()
            failed_smiles_fetch = []

            for molecule in self.molecules:
                try:
                    smiles = get_molecule_smiles(molecule, self.config)
                    if smiles:
                        self.molecule_smiles_map[molecule] = smiles
                    else:
                        failed_smiles_fetch.append(molecule)
                        self.logger.warning(
                            f"Could not fetch SMILES for molecule: {molecule}"
                        )
                except Exception as e:
                    failed_smiles_fetch.append(molecule)
                    self.logger.error(f"Error fetching SMILES for {molecule}: {e}")

            # Handle molecules that failed SMILES fetch
            if failed_smiles_fetch:
                rich_print(
                    f"[yellow]⚠️  Não foi possível obter SMILES para "
                    f"{len(failed_smiles_fetch)} moléculas:[/yellow]"
                )
                for failed in failed_smiles_fetch:
                    rich_print(f"   • {failed}")

                choice = questionary.select(
                    "Como deseja proceder com as moléculas sem SMILES?",
                    choices=[
                        "Continuar (remover moléculas sem SMILES)",
                        "Voltar para o modo de edição",
                        "Cancelar operação",
                    ],
                ).ask()

                if choice == "Voltar para o modo de edição":
                    return False
                elif choice == "Cancelar operação":
                    return False
                else:
                    # Remove failed molecules from the list
                    self.molecules = [
                        m for m in self.molecules if m not in failed_smiles_fetch
                    ]
                    # Clear their entries from SMILES map (if any)
                    for failed in failed_smiles_fetch:
                        self.molecule_smiles_map.pop(failed, None)

                    if not self.molecules:
                        rich_print(
                            "[yellow]⚠️  Lista ficou vazia após remover moléculas sem "
                            "SMILES[/yellow]"
                        )
                        return False

            rich_print(
                f"[green]✅ SMILES obtido para {len(self.molecule_smiles_map)} "
                f"moléculas[/green]"
            )
            return True

        except Exception as e:
            self.logger.error(f"Error during SMILES conversion: {e}")
            rich_print(f"[red]❌ Erro na conversão para SMILES: {e}[/red]")
            return False

    def _validate_database_duplicates(self) -> bool:
        """
        Validate against database duplicates using pre-converted SMILES.

        This method assumes SMILES conversion has already been completed
        by _convert_molecules_to_smiles().

        Returns:
            True to continue, False to cancel or return to editing
        """
        rich_print(
            "[yellow]📋 Verificando duplicatas no banco de dados PM7...[/yellow]"
        )

        try:
            existing_smiles = database_service.get_existing_smiles(self.pm7_db_path)

            # Perform SMILES-based duplicate checking using pre-converted SMILES
            duplicates = []
            for molecule in self.molecules:
                if molecule in self.molecule_smiles_map:
                    molecule_smiles = self.molecule_smiles_map[molecule]
                    if molecule_smiles in existing_smiles:
                        duplicates.append(molecule)

            if not duplicates:
                rich_print(
                    "[green]✅ Nenhuma duplicata encontrada no banco de dados[/green]"
                )
                return True

            rich_print(
                f"[yellow]⚠️  Encontradas {len(duplicates)} possíveis "
                f"duplicatas:[/yellow]"
            )
            for dup in duplicates:
                rich_print(f"   • {dup}")

            choice = questionary.select(
                "Como deseja proceder com as duplicatas?",
                choices=[
                    "Sobrescrever todas (recalcular)",
                    "Manter todas (pular duplicatas)",
                    "Escolher individualmente",
                    "Voltar para o modo de edição",
                ],
            ).ask()

            if choice == "Voltar para o modo de edição":
                return False
            elif choice == "Sobrescrever todas (recalcular)":
                # Mark all duplicates for overwrite
                self.molecules_to_overwrite.update(duplicates)
                rich_print(
                    f"[green]✅ {len(duplicates)} moléculas marcadas para "
                    f"sobrescrever[/green]"
                )
            elif choice == "Manter todas (pular duplicatas)":
                # Remove duplicates from the list and SMILES mapping
                self.molecules = [m for m in self.molecules if m not in duplicates]
                for dup in duplicates:
                    self.molecule_smiles_map.pop(dup, None)
                    self.molecules_to_overwrite.discard(
                        dup
                    )  # Remove from overwrite set if present
                rich_print(
                    f"[green]✅ {len(duplicates)} duplicatas removidas da lista[/green]"
                )
                if not self.molecules:
                    rich_print(
                        "[yellow]⚠️  Lista ficou vazia após remover duplicatas[/yellow]"
                    )
                    return False
            elif choice == "Escolher individualmente":
                # Use clearer wording for individual selection
                selected = questionary.checkbox(
                    "Selecione as moléculas duplicadas que deseja PROCESSAR "
                    "(as não selecionadas serão removidas):",
                    choices=duplicates,
                ).ask()

                # Handle the case where user selects nothing (cancel/empty selection)
                if selected is None:
                    # User cancelled - return to editing mode
                    return False

                # Handle selected molecules (ask if they want to overwrite)
                if selected:
                    overwrite_choice = questionary.select(
                        f"Como proceder com as {len(selected)} moléculas selecionadas?",
                        choices=[
                            "Sobrescrever (recalcular)",
                            "Pular (manter dados existentes)",
                        ],
                    ).ask()

                    if overwrite_choice == "Sobrescrever (recalcular)":
                        self.molecules_to_overwrite.update(selected)
                        rich_print(
                            f"[green]✅ {len(selected)} moléculas marcadas para "
                            f"sobrescrever[/green]"
                        )
                    else:
                        # Remove selected molecules from the list (don't process them)
                        self.molecules = [
                            m for m in self.molecules if m not in selected
                        ]
                        for sel in selected:
                            self.molecule_smiles_map.pop(sel, None)
                            self.molecules_to_overwrite.discard(sel)
                        rich_print(
                            f"[green]✅ {len(selected)} duplicatas puladas[/green]"
                        )

                # Remove unselected duplicates from processing
                to_remove = [m for m in duplicates if m not in selected]
                if to_remove:
                    self.molecules = [m for m in self.molecules if m not in to_remove]
                    for removed in to_remove:
                        self.molecule_smiles_map.pop(removed, None)
                        self.molecules_to_overwrite.discard(removed)
                    rich_print(
                        f"[green]✅ {len(to_remove)} duplicatas removidas da "
                        f"lista[/green]"
                    )

                # Check if list is empty after processing
                if not self.molecules:
                    rich_print(
                        "[yellow]⚠️  Lista ficou vazia após processar "
                        "duplicatas[/yellow]"
                    )
                    return False

                # If no molecules were selected, inform user
                if not selected:
                    rich_print(
                        "[yellow]ℹ️  Nenhuma molécula selecionada - todas as "
                        "duplicatas foram removidas[/yellow]"
                    )

            return True

        except Exception as e:
            self.logger.error(f"Error validating database duplicates: {e}")
            rich_print(f"[red]❌ Erro na validação de duplicatas: {e}[/red]")
            return False

    def _reset_validation_state(self) -> None:
        """
        Reset validation state when molecule list is modified.

        This ensures that validation is re-run completely when the list changes.
        """
        self.molecule_smiles_map.clear()
        self.molecules_to_overwrite.clear()
        self._validation_completed = False

    def _validate_pubchem_availability(self) -> bool:
        """
        Validate molecules are available on PubChem.

        Returns:
            True to continue processing, False to cancel or return to editing
        """
        rich_print("[yellow]🔬 Verificando disponibilidade no PubChem...[/yellow]")

        not_found = []
        found_count = 0

        for molecule in self.molecules:
            try:
                # Simple check using pubchem service search
                import pubchempy as pcp

                compounds = pcp.get_compounds(molecule, "name")
                if not compounds:
                    not_found.append(molecule)
                else:
                    found_count += 1
            except Exception as e:
                self.logger.warning(f"Error checking PubChem for {molecule}: {e}")
                not_found.append(molecule)

        if not not_found:
            rich_print(
                f"[green]✅ Todas as {found_count} moléculas encontradas no "
                f"PubChem[/green]"
            )
            return True

        rich_print(
            f"[yellow]⚠️  {len(not_found)} moléculas não encontradas no "
            f"PubChem:[/yellow]"
        )
        for nf in not_found:
            rich_print(f"   • {nf}")

        choice = questionary.select(
            "Como deseja proceder com as moléculas não encontradas?",
            choices=[
                "Continuar (ignorando e salvando em not-found.txt)",
                "Voltar para o modo de edição",
                "Cancelar operação",
            ],
        ).ask()

        if choice == "Voltar para o modo de edição":
            return False
        elif choice == "Cancelar operação":
            return False
        else:
            # Save not found molecules and remove from list and SMILES mapping
            self._save_not_found_molecules(not_found)
            self.molecules = [m for m in self.molecules if m not in not_found]
            # Also remove from SMILES mapping
            for nf in not_found:
                self.molecule_smiles_map.pop(nf, None)

            if not self.molecules:
                rich_print(
                    "[yellow]⚠️  Lista ficou vazia após remover moléculas não "
                    "encontradas[/yellow]"
                )
                return False

            rich_print(
                f"[green]✅ Continuando com {len(self.molecules)} moléculas "
                f"válidas[/green]"
            )
            return True

    def _save_not_found_molecules(self, not_found: List[str]) -> None:
        """Save not found molecules to not-found.txt file."""
        try:
            not_found_file = self.not_found_dir / "not-found.txt"

            # Read existing content if file exists
            existing = []
            if not_found_file.exists():
                with open(not_found_file, "r", encoding="utf-8") as f:
                    existing = [line.strip() for line in f if line.strip()]

            # Add new not found molecules (avoid duplicates)
            for molecule in not_found:
                if molecule not in existing:
                    existing.append(molecule)

            # Write back
            with open(not_found_file, "w", encoding="utf-8") as f:
                for molecule in existing:
                    f.write(f"{molecule}\n")

            rich_print(
                f"[blue]ℹ️  Moléculas não encontradas salvas em: "
                f"{not_found_file}[/blue]"
            )

        except Exception as e:
            self.logger.error(f"Error saving not found molecules: {e}")
            rich_print(f"[red]❌ Erro ao salvar moléculas não encontradas: {e}[/red]")

    def _start_batch_processing(self) -> bool:
        """
        Save the final list and start batch processing.

        Returns:
            True if processing started successfully
        """
        try:
            # Create backup if editing existing file
            if self.current_file:
                original_path = self.lists_dir / self.current_file
                backup_path = self.lists_dir / f"{self.current_file}.bak"
                shutil.copy2(original_path, backup_path)
                rich_print(f"[blue]ℹ️  Backup criado: {backup_path.name}[/blue]")

                # Save to original file
                final_file = original_path
            else:
                # Ask for filename for new list
                filename = questionary.text(
                    "Digite um nome para salvar a lista (sem extensão):",
                    validate=lambda text: len(text.strip()) > 0
                    or "Nome não pode estar vazio",
                ).ask()

                if not filename:
                    return False

                # Sanitize filename
                filename = "".join(
                    c for c in filename.strip() if c.isalnum() or c in (" ", "-", "_")
                ).rstrip()
                final_file = self.lists_dir / f"{filename}.txt"

            # Save final list
            with open(final_file, "w", encoding="utf-8") as f:
                for molecule in self.molecules:
                    f.write(f"{molecule}\n")

            rich_print(f"[green]✅ Lista final salva: {final_file.name}[/green]")
            rich_print(
                f"[green]🚀 Iniciando processamento de {len(self.molecules)} "
                f"moléculas...[/green]"
            )

            # Start actual batch processing with progress bar
            successful_count = 0
            failed_count = 0

            from rich.progress import Progress, TextColumn, BarColumn, TimeElapsedColumn

            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TextColumn("({task.completed}/{task.total})"),
                TimeElapsedColumn(),
            ) as progress:

                task = progress.add_task(
                    "Processando moléculas...", total=len(self.molecules)
                )

                for i, molecule in enumerate(self.molecules):
                    progress.update(
                        task, description=f"Processando: {molecule[:30]}..."
                    )

                    try:
                        # Determine if this molecule should be overwritten
                        should_overwrite = molecule in self.molecules_to_overwrite
                        success = process_single_molecule(
                            molecule, self.config, overwrite=should_overwrite
                        )
                        if success:
                            successful_count += 1
                        else:
                            failed_count += 1
                    except Exception as e:
                        failed_count += 1
                        self.logger.error(f"Error processing {molecule}: {e}")

                    progress.update(task, advance=1)

            # Display final results
            from rich.table import Table

            results_table = Table(title="Resultados do Processamento em Lote")
            results_table.add_column("Métrica", style="bold")
            results_table.add_column("Quantidade", justify="right")
            results_table.add_column("Porcentagem", justify="right")

            total = len(self.molecules)
            success_pct = (successful_count / total) * 100 if total > 0 else 0
            failed_pct = (failed_count / total) * 100 if total > 0 else 0

            results_table.add_row("Total de Moléculas", str(total), "100.0%")
            results_table.add_row(
                "Processadas com Sucesso",
                str(successful_count),
                f"{success_pct:.1f}%",
                style="green",
            )
            results_table.add_row(
                "Falharam", str(failed_count), f"{failed_pct:.1f}%", style="red"
            )

            self.console.print()
            self.console.print(results_table)

            if successful_count > 0:
                rich_print(
                    f"[green]🎉 Processamento concluído! {successful_count} "
                    f"moléculas processadas com sucesso.[/green]"
                )

            if failed_count > 0:
                rich_print(
                    f"[yellow]⚠️  {failed_count} moléculas falharam no "
                    f"processamento. Verifique os logs para detalhes.[/yellow]"
                )

            return True

        except Exception as e:
            self.logger.error(f"Error starting batch processing: {e}")
            rich_print(f"[red]❌ Erro ao iniciar processamento: {e}[/red]")
            return False


def run_interactive_batch(config: Dict[str, Any]) -> bool:
    """
    Run the interactive batch workflow.

    Args:
        config: Configuration dictionary

    Returns:
        True if batch processing should start, False if cancelled
    """
    workflow = InteractiveBatchWorkflow(config)
    return workflow.run()
