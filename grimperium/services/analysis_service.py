"""
Analysis service for Grimperium computational chemistry workflow insights.

This module provides functionality to analyze progress and coverage of
computational chemistry calculations by comparing reference databases
with calculated results, generating comprehensive progress reports.
"""

import logging
from typing import Dict, Any, Optional

from .database_service import get_existing_smiles, get_database_stats
from ..constants import (
    DEFAULT_TIME_PER_MOLECULE,
    SECONDS_PER_HOUR,
    TIME_DISPLAY_THRESHOLDS,
)


def generate_progress_report(cbs_db_path: str, pm7_db_path: str) -> Dict[str, Any]:
    """
    Generate comprehensive progress report comparing CBS reference and PM7
    calculated databases.

    This function analyzes the coverage of computational chemistry calculations
    by comparing the CBS reference database with the PM7 calculated database,
    providing insights into progress and completion status.

    Args:
        cbs_db_path: Path to the CBS reference database CSV file
        pm7_db_path: Path to the PM7 calculated results database CSV file

    Returns:
        Dictionary containing progress metrics:
        - total_cbs: Number of unique SMILES in CBS reference database
        - total_pm7: Number of unique SMILES in PM7 calculated database
        - common_count: Number of SMILES present in both databases
        - progress_percentage: Completion percentage (common/total_cbs * 100)
        - missing_count: Number of SMILES in CBS but not in PM7
        - extra_count: Number of SMILES in PM7 but not in CBS
        - cbs_exists: Whether CBS database file exists
        - pm7_exists: Whether PM7 database file exists

    Example:
        >>> report = generate_progress_report("data/cbs.csv", "data/pm7.csv")
        >>> print(f"Progress: {report['progress_percentage']:.1f}%")
        Progress: 15.7%
    """
    logger = logging.getLogger(__name__)

    try:
        logger.info("Generating progress report...")
        logger.debug(f"CBS database path: {cbs_db_path}")
        logger.debug(f"PM7 database path: {pm7_db_path}")

        # Get existing SMILES from both databases
        cbs_smiles = get_existing_smiles(cbs_db_path)
        pm7_smiles = get_existing_smiles(pm7_db_path)

        # Check if databases exist
        from pathlib import Path

        cbs_exists = Path(cbs_db_path).exists()
        pm7_exists = Path(pm7_db_path).exists()

        logger.debug(
            f"CBS database exists: {cbs_exists}, " f"SMILES count: {len(cbs_smiles)}"
        )
        logger.debug(
            f"PM7 database exists: {pm7_exists}, " f"SMILES count: {len(pm7_smiles)}"
        )

        # Calculate basic metrics
        total_cbs = len(cbs_smiles)
        total_pm7 = len(pm7_smiles)

        # Calculate intersection and differences
        common_smiles = cbs_smiles.intersection(pm7_smiles)
        common_count = len(common_smiles)

        # Calculate missing and extra molecules
        missing_smiles = cbs_smiles - pm7_smiles  # In CBS but not in PM7
        extra_smiles = pm7_smiles - cbs_smiles  # In PM7 but not in CBS
        missing_count = len(missing_smiles)
        extra_count = len(extra_smiles)

        # Calculate progress percentage
        if total_cbs > 0:
            progress_percentage = (common_count / total_cbs) * 100
        else:
            progress_percentage = 0.0

        # Log progress information
        logger.info("Progress analysis complete:")
        logger.info(f"  CBS molecules: {total_cbs}")
        logger.info(f"  PM7 molecules: {total_pm7}")
        logger.info(f"  Common molecules: {common_count}")
        logger.info(f"  Progress: {progress_percentage:.2f}%")

        if missing_count > 0:
            logger.info(f"  Remaining to calculate: {missing_count}")
        if extra_count > 0:
            logger.info(f"  Extra calculations (not in CBS): {extra_count}")

        # Compile comprehensive report
        report = {
            "total_cbs": total_cbs,
            "total_pm7": total_pm7,
            "common_count": common_count,
            "missing_count": missing_count,
            "extra_count": extra_count,
            "progress_percentage": progress_percentage,
            "cbs_exists": cbs_exists,
            "pm7_exists": pm7_exists,
            "cbs_db_path": cbs_db_path,
            "pm7_db_path": pm7_db_path,
        }

        return report

    except Exception as e:
        logger.error(f"Error generating progress report: {e}")
        # Return safe default values in case of error
        return {
            "total_cbs": 0,
            "total_pm7": 0,
            "common_count": 0,
            "missing_count": 0,
            "extra_count": 0,
            "progress_percentage": 0.0,
            "cbs_exists": False,
            "pm7_exists": False,
            "error": str(e),
            "cbs_db_path": cbs_db_path,
            "pm7_db_path": pm7_db_path,
        }


def get_detailed_database_analysis(db_path: str) -> Dict[str, Any]:
    """
    Get detailed analysis of a single database file.

    This function provides comprehensive statistics about a database file,
    including file information, content analysis, and data quality metrics.

    Args:
        db_path: Path to the database CSV file

    Returns:
        Dictionary containing detailed database analysis
    """
    logger = logging.getLogger(__name__)

    try:
        # Get basic database statistics
        stats = get_database_stats(db_path)

        if not stats.get("exists", False):
            return {
                "exists": False,
                "path": db_path,
                "error": stats.get("error", "Database file does not exist"),
            }

        # Get SMILES for additional analysis
        smiles_set = get_existing_smiles(db_path)

        # Calculate additional metrics
        analysis = {
            "exists": True,
            "path": db_path,
            "total_entries": stats.get("total_entries", 0),
            "unique_smiles": len(smiles_set),
            "file_size_bytes": stats.get("file_size_bytes", 0),
            "file_size_mb": stats.get("file_size_bytes", 0) / (1024 * 1024),
            "columns": stats.get("columns", []),
            "column_count": len(stats.get("columns", [])),
        }

        # Calculate data quality metrics
        total_entries = analysis["total_entries"]
        unique_smiles = analysis["unique_smiles"]

        if total_entries > 0:
            analysis["duplicate_ratio"] = 1 - (unique_smiles / total_entries)
            analysis["data_quality"] = (
                "Good" if analysis["duplicate_ratio"] < 0.1 else "Needs Review"
            )
        else:
            analysis["duplicate_ratio"] = 0.0
            analysis["data_quality"] = "Empty"

        logger.debug(f"Database analysis complete for: {db_path}")
        return analysis

    except Exception as e:
        logger.error(f"Error analyzing database {db_path}: {e}")
        return {"exists": False, "path": db_path, "error": str(e)}


def find_missing_molecules(
    cbs_db_path: str, pm7_db_path: str, limit: Optional[int] = None
) -> list[str]:
    """
    Find molecules that are in the CBS database but missing from PM7
    calculations.

    This function identifies which molecules from the reference database
    still need to be calculated, useful for planning future batch runs.

    Args:
        cbs_db_path: Path to the CBS reference database
        pm7_db_path: Path to the PM7 calculated database
        limit: Maximum number of missing molecules to return (None for all)

    Returns:
        List of SMILES strings that need to be calculated
    """
    logger = logging.getLogger(__name__)

    try:
        # Get SMILES from both databases
        cbs_smiles = get_existing_smiles(cbs_db_path)
        pm7_smiles = get_existing_smiles(pm7_db_path)

        # Find missing molecules
        missing_smiles = cbs_smiles - pm7_smiles
        missing_list = sorted(list(missing_smiles))

        # Apply limit if specified
        if limit is not None and limit > 0:
            missing_list = missing_list[:limit]

        logger.info(
            f"Found {len(missing_smiles)} missing molecules, "
            f"returning {len(missing_list)}"
        )
        return missing_list

    except Exception as e:
        logger.error(f"Error finding missing molecules: {e}")
        return []


def calculate_completion_eta(
    total_remaining: int,
    recent_completion_rate: float,
    time_per_molecule: float = DEFAULT_TIME_PER_MOLECULE,
) -> Dict[str, Any]:
    """
    Calculate estimated time to completion based on current progress.

    Args:
        total_remaining: Number of molecules remaining to calculate
        recent_completion_rate: Recent completion rate (molecules per hour)
        time_per_molecule: Average time per molecule in seconds

    Returns:
        Dictionary with ETA estimates
    """
    logger = logging.getLogger(__name__)

    try:
        if total_remaining <= 0:
            return {
                "eta_hours": 0,
                "eta_days": 0,
                "eta_human": "Complete!",
                "completion_rate_per_hour": recent_completion_rate,
            }

        # Calculate ETA based on completion rate
        if recent_completion_rate > 0:
            eta_hours = total_remaining / recent_completion_rate
        else:
            # Fallback to time per molecule estimate
            eta_hours = (total_remaining * time_per_molecule) / SECONDS_PER_HOUR

        eta_days = eta_hours / (TIME_DISPLAY_THRESHOLDS["days"] / SECONDS_PER_HOUR)

        # Create human-readable ETA
        if eta_hours < 1:
            eta_human = (
                f"{eta_hours * TIME_DISPLAY_THRESHOLDS['minutes']:.0f} " "minutes"
            )
        elif eta_hours < (TIME_DISPLAY_THRESHOLDS["days"] / SECONDS_PER_HOUR):
            eta_human = f"{eta_hours:.1f} hours"
        elif eta_days < 7:
            eta_human = f"{eta_days:.1f} days"
        else:
            eta_human = f"{eta_days / 7:.1f} weeks"

        return {
            "eta_hours": eta_hours,
            "eta_days": eta_days,
            "eta_human": eta_human,
            "completion_rate_per_hour": recent_completion_rate,
            "total_remaining": total_remaining,
        }

    except Exception as e:
        logger.error(f"Error calculating completion ETA: {e}")
        return {
            "eta_hours": 0,
            "eta_days": 0,
            "eta_human": "Unknown",
            "error": str(e),
        }
