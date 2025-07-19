"""
Core domain model for molecular representation in Grimperium.

This module defines the Molecule class, which serves as the central data
structure
for representing chemical compounds throughout the computational chemistry
pipeline.
The molecule object tracks all relevant paths, properties, and computed values
as they are generated during the workflow.
"""

from typing import Optional
from pydantic import BaseModel, Field


class Molecule(BaseModel):
    """
    Core domain model representing a chemical molecule and its associated data.

    This class serves as the central data structure for the Grimperium
    computational
    chemistry pipeline. It tracks the molecule's identity, file paths for
    various
    formats, and computed properties as they are generated throughout the
    workflow.

    The class uses Pydantic for robust data validation and serialization,
    ensuring
    type safety and data integrity throughout the pipeline operations.

    Attributes:
        identifier: The initial molecule identifier (name, SMILES, etc.)
        smiles: Canonical SMILES representation of the molecule
        sdf_path: Path to the SDF structure file
        xyz_path: Path to the XYZ coordinate file
        crest_best_xyz_path: Path to the best conformer from CREST
            optimization
        pm7_energy: Computed PM7 energy value in kcal/mol
        charge: Molecular charge (default: 0)
        multiplicity: Spin multiplicity (default: 1 for singlet)
    """

    identifier: str = Field(
        ...,
        description=("Initial molecule identifier (name, SMILES, or other identifier)"),
    )

    smiles: Optional[str] = Field(
        None, description="Canonical SMILES representation of the molecule"
    )

    sdf_path: Optional[str] = Field(
        None, description="Path to the molecule's SDF structure file"
    )

    xyz_path: Optional[str] = Field(
        None, description="Path to the molecule's XYZ coordinate file"
    )

    crest_best_xyz_path: Optional[str] = Field(
        None,
        description=("Path to the best conformer XYZ file from CREST optimization"),
    )

    pm7_energy: Optional[float] = Field(
        None, description="Computed PM7 energy value in kcal/mol"
    )

    charge: Optional[int] = Field(
        0,
        description="Molecular charge (default: 0 for neutral molecules)",
    )

    multiplicity: Optional[int] = Field(
        1, description="Spin multiplicity (default: 1 for singlet state)"
    )

    class Config:
        """Pydantic configuration for the Molecule model."""

        validate_assignment = True
        use_enum_values = True

    def __str__(self) -> str:
        """Return a human-readable string representation of the molecule."""
        return f"Molecule(identifier='{self.identifier}', " f"smiles='{self.smiles}')"

    def __repr__(self) -> str:
        """Return a detailed string representation for debugging."""
        return (
            f"Molecule("
            f"identifier='{self.identifier}', "
            f"smiles='{self.smiles}', "
            f"charge={self.charge}, "
            f"multiplicity={self.multiplicity}"
            f")"
        )
