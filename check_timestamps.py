"""
Timestamp Consistency Checker for YouTube Traffic Data CSV Files.

This script validates that all CSV files in a directory have consistent timestamps.
"""

import argparse
import csv
import logging
import os
from typing import Optional, Set, List
from pathlib import Path

from utils import parse_datetime_string, setup_logging


logger = logging.getLogger(__name__)


def get_timestamps_from_csv(filepath: str) -> Optional[Set]:
    """
    Extracts timestamps from the 'date and time' column of a CSV file.

    Args:
        filepath: Path to the CSV file.

    Returns:
        Set of datetime objects if successful, None if errors occur.
    """
    timestamps = set()

    try:
        with open(filepath, 'r', encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile)
            header = next(csv_reader, None)

            if header is None:
                logger.warning(f"CSV file '{filepath}' is empty")
                return None

            if 'date and time' not in header:
                logger.warning(f"'date and time' column not found in '{filepath}'. Header: {header}")
                return None

            for row_num, row in enumerate(csv_reader, start=2):
                if not row:
                    continue

                datetime_str = row[0]
                datetime_obj = parse_datetime_string(datetime_str)

                if datetime_obj is None:
                    logger.error(f"Could not parse datetime '{datetime_str}' in '{filepath}' at row {row_num}")
                    return None

                timestamps.add(datetime_obj)

    except Exception as e:
        logger.error(f"Error reading CSV file '{filepath}': {e}")
        return None

    return timestamps


def compare_timestamps(
    reference_timestamps: Set,
    current_timestamps: Set,
    reference_filename: str,
    current_filename: str
) -> bool:
    """
    Compares two sets of timestamps and logs any differences.

    Args:
        reference_timestamps: Reference set of timestamps.
        current_timestamps: Current set of timestamps to compare.
        reference_filename: Name of the reference file.
        current_filename: Name of the current file.

    Returns:
        True if timestamps match, False otherwise.
    """
    if current_timestamps == reference_timestamps:
        logger.info(f"Timestamps in '{current_filename}' match the reference")
        return True

    missing_timestamps = reference_timestamps - current_timestamps
    extra_timestamps = current_timestamps - reference_timestamps

    if missing_timestamps:
        logger.error(
            f"'{current_filename}' is missing {len(missing_timestamps)} timestamps "
            f"compared to '{reference_filename}'"
        )
        for ts in sorted(list(missing_timestamps))[:5]:
            logger.error(f"  Missing: {ts}")
        if len(missing_timestamps) > 5:
            logger.error(f"  ... and {len(missing_timestamps) - 5} more")

    if extra_timestamps:
        logger.error(
            f"'{current_filename}' has {len(extra_timestamps)} extra timestamps "
            f"compared to '{reference_filename}'"
        )
        for ts in sorted(list(extra_timestamps))[:5]:
            logger.error(f"  Extra: {ts}")
        if len(extra_timestamps) > 5:
            logger.error(f"  ... and {len(extra_timestamps) - 5} more")

    # Check for different timestamps at same positions (edge case)
    if not missing_timestamps and not extra_timestamps:
        reference_list = sorted(list(reference_timestamps))
        current_list = sorted(list(current_timestamps))
        different_count = 0

        for i in range(min(len(reference_list), len(current_list))):
            if reference_list[i] != current_list[i]:
                different_count += 1

        if different_count > 0:
            logger.error(
                f"'{current_filename}' has {different_count} different timestamps "
                f"at the same positions compared to '{reference_filename}'"
            )

    return False


def check_timestamps(input_directory: str) -> bool:
    """
    Checks timestamp consistency across all CSV files in a directory.

    Args:
        input_directory: Path to the directory containing CSV files.

    Returns:
        True if all files have consistent timestamps, False otherwise.
    """
    if not os.path.exists(input_directory):
        logger.error(f"Directory '{input_directory}' not found")
        return False

    csv_files = sorted([f for f in os.listdir(input_directory) if f.endswith('.csv')])

    if not csv_files:
        logger.error(f"No CSV files found in '{input_directory}'")
        return False

    logger.info(f"Found {len(csv_files)} CSV files to check")

    reference_timestamps = None
    reference_filename = ""
    all_match = True
    skipped_count = 0

    for filename in csv_files:
        filepath = os.path.join(input_directory, filename)
        current_timestamps = get_timestamps_from_csv(filepath)

        if current_timestamps is None:
            logger.warning(f"Skipping comparison for '{filename}' due to errors")
            skipped_count += 1
            all_match = False
            continue

        if reference_timestamps is None:
            reference_timestamps = current_timestamps
            reference_filename = filename
            logger.info(f"Using timestamps from '{reference_filename}' as reference ({len(reference_timestamps)} timestamps)")
        else:
            if not compare_timestamps(reference_timestamps, current_timestamps, reference_filename, filename):
                all_match = False

    # Summary
    logger.info("=" * 60)
    logger.info("Timestamp Check Summary:")
    logger.info(f"  Total files: {len(csv_files)}")
    logger.info(f"  Files checked: {len(csv_files) - skipped_count}")
    logger.info(f"  Files skipped: {skipped_count}")
    logger.info(f"  All timestamps consistent: {all_match}")
    logger.info("=" * 60)

    return all_match


def parse_arguments() -> argparse.Namespace:
    """
    Parses command-line arguments.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Check timestamp consistency across CSV files in a directory",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        'input_dir',
        help='Path to the directory containing CSV files'
    )

    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level'
    )

    parser.add_argument(
        '--log-file',
        type=str,
        default=None,
        help='Path to log file (logs to console if not specified)'
    )

    return parser.parse_args()


def main() -> None:
    """Main execution function."""
    args = parse_arguments()

    # Setup logging
    log_level = getattr(logging, args.log_level)
    setup_logging(level=log_level, log_file=args.log_file)

    logger.info("Starting timestamp consistency check")

    # Check timestamps
    success = check_timestamps(args.input_dir)

    if success:
        logger.info("Timestamp check completed successfully - all files are consistent")
    else:
        logger.error("Timestamp check completed with errors - inconsistencies found")
        exit(1)


if __name__ == '__main__':
    main()
