"""
CSV Merger for YouTube Traffic Data.

This script merges multiple country-specific CSV files into a single consolidated CSV file.
"""

import argparse
import csv
import logging
import os
from typing import Dict, List, Set
from pathlib import Path
from collections import defaultdict

from utils import parse_datetime_string, format_datetime, setup_logging


logger = logging.getLogger(__name__)


class MergeStats:
    """Tracks merge statistics."""

    def __init__(self):
        self.files_processed = 0
        self.files_failed = 0
        self.total_timestamps = 0
        self.total_countries = 0
        self.failed_files: List[str] = []

    def add_success(self, filename: str) -> None:
        """Record a successfully processed file."""
        self.files_processed += 1

    def add_failure(self, filename: str) -> None:
        """Record a failed file."""
        self.files_failed += 1
        self.failed_files.append(filename)

    def print_summary(self) -> None:
        """Print merge statistics summary."""
        logger.info("=" * 60)
        logger.info("Merge Summary:")
        logger.info(f"  Files processed: {self.files_processed}")
        logger.info(f"  Files failed: {self.files_failed}")
        logger.info(f"  Total countries: {self.total_countries}")
        logger.info(f"  Total timestamps: {self.total_timestamps}")

        if self.failed_files:
            logger.warning(f"\nFailed files ({len(self.failed_files)}):")
            for filename in self.failed_files[:10]:
                logger.warning(f"  - {filename}")
            if len(self.failed_files) > 10:
                logger.warning(f"  ... and {len(self.failed_files) - 10} more")
        logger.info("=" * 60)


def read_csv_file(filepath: str, country_code: str) -> Dict[str, str]:
    """
    Reads a country CSV file and returns a dictionary of timestamp -> value.

    Args:
        filepath: Path to the CSV file.
        country_code: Country code for logging purposes.

    Returns:
        Dictionary mapping timestamp strings to values.
    """
    data = {}

    try:
        with open(filepath, 'r', encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile)
            header = next(csv_reader, None)

            if header is None:
                logger.warning(f"Empty CSV file: {filepath}")
                return data

            for row_num, row in enumerate(csv_reader, start=2):
                if not row or len(row) < 2:
                    continue

                datetime_str = row[0]
                value = row[1]

                # Parse and reformat to ensure consistency
                datetime_obj = parse_datetime_string(datetime_str)
                if datetime_obj is None:
                    logger.warning(f"Could not parse datetime '{datetime_str}' in {filepath} at row {row_num}")
                    continue

                # Use consistent format as key
                datetime_key = format_datetime(datetime_obj, include_ms=True)
                data[datetime_key] = value

        logger.debug(f"Read {len(data)} data points from {country_code}.csv")

    except Exception as e:
        logger.error(f"Error reading {filepath}: {e}")

    return data


def merge_csv_files(input_dir: str, output_filepath: str) -> bool:
    """
    Merges multiple CSV files from input_dir into a single CSV file.

    Args:
        input_dir: Directory containing CSV files to merge.
        output_filepath: Path to save the merged CSV file.

    Returns:
        True if merge was successful, False otherwise.
    """
    if not os.path.exists(input_dir):
        logger.error(f"Input directory '{input_dir}' not found")
        return False

    csv_files = sorted([f for f in os.listdir(input_dir) if f.endswith('.csv')])

    if not csv_files:
        logger.error(f"No CSV files found in '{input_dir}'")
        return False

    logger.info(f"Found {len(csv_files)} CSV files to merge")

    # Data structure: {timestamp: {country_code: value}}
    merged_data: Dict[str, Dict[str, str]] = defaultdict(dict)
    country_codes: List[str] = []
    stats = MergeStats()

    # Read all CSV files
    for filename in csv_files:
        country_code = filename[:-4]  # Remove .csv extension
        filepath = os.path.join(input_dir, filename)

        logger.debug(f"Processing {filename}")

        country_data = read_csv_file(filepath, country_code)

        if not country_data:
            logger.warning(f"No data read from {filename}")
            stats.add_failure(filename)
            continue

        country_codes.append(country_code)
        stats.add_success(filename)

        # Add country data to merged data
        for timestamp, value in country_data.items():
            merged_data[timestamp][country_code] = value

    if not merged_data:
        logger.error("No data to merge")
        return False

    # Sort timestamps and country codes
    sorted_timestamps = sorted(merged_data.keys())
    sorted_country_codes = sorted(country_codes)

    stats.total_countries = len(sorted_country_codes)
    stats.total_timestamps = len(sorted_timestamps)

    logger.info(f"Merging {len(sorted_country_codes)} countries across {len(sorted_timestamps)} timestamps")

    # Write merged CSV
    try:
        with open(output_filepath, 'w', newline='', encoding='utf-8') as outfile:
            csv_writer = csv.writer(outfile)

            # Write header
            header_row = ['date and time'] + sorted_country_codes
            csv_writer.writerow(header_row)

            # Write data rows
            for timestamp in sorted_timestamps:
                row = [timestamp]
                for country_code in sorted_country_codes:
                    value = merged_data[timestamp].get(country_code, 'NA')
                    row.append(value)
                csv_writer.writerow(row)

        logger.info(f"Merged data saved to '{output_filepath}'")
        stats.print_summary()
        return True

    except Exception as e:
        logger.error(f"Error writing merged CSV file: {e}")
        return False


def parse_arguments() -> argparse.Namespace:
    """
    Parses command-line arguments.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Merge CSV files from a directory into a single CSV",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        'input_dir',
        help='Path to the directory containing CSV files to merge'
    )

    parser.add_argument(
        'output_file',
        help='Path to save the merged CSV file'
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

    logger.info("Starting CSV merge process")

    # Merge files
    success = merge_csv_files(args.input_dir, args.output_file)

    if success:
        logger.info("Merge process completed successfully")
    else:
        logger.error("Merge process completed with errors")
        exit(1)


if __name__ == '__main__':
    main()
