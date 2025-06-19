"""
Script to check timestamp consistency across multiple CSV files in a directory.

This script iterates through all CSV files in a specified input directory,
extracts timestamps from a 'date and time' column, and compares these
timestamps against a reference file (the first one processed). It reports
any inconsistencies, such as missing, extra, or different timestamps.
"""
import csv
import os
import datetime
import argparse
from typing import Set, Optional, List, Any  # Added for type hints


def get_timestamps_from_csv(filepath: str) -> Optional[Set[datetime.datetime]]:
    """
    Extracts and parses timestamps from the 'date and time' column of a CSV file.

    The function expects the 'date and time' column to be the first column.
    It attempts to parse timestamps with and without milliseconds.

    Args:
        filepath: The path to the CSV file.

    Returns:
        A set of datetime.datetime objects if successful.
        None if the file is empty, the required column is missing,
        a read error occurs, or any timestamp is unparseable.
        Prints warnings or errors to stdout in case of issues.
    """
    timestamps: Set[datetime.datetime] = set()
    try:
        with open(filepath, 'r', encoding='utf-8') as csvfile:
            csv_reader: Any = csv.reader(csvfile)  # csv.reader is tricky to type
            header: Optional[List[str]] = next(csv_reader, None)

            if header is None:
                print(f"Warning: CSV file '{filepath}' is empty.")
                return None
            if 'date and time' not in header:
                print(f"Warn: 'date and time' missing in {filepath}.")  # Max shorten
                print(f"Header: {header}")
                return None

            # Format with milliseconds
            datetime_format = '%Y-%m-%d %H:%M:%S.%f'
            # Format without milliseconds
            datetime_format_no_ms = '%Y-%m-%d %H:%M:%S'

            for row in csv_reader:
                if row:  # Ensure row is not empty
                    datetime_str: str = row[0]
                    try:
                        dt_obj = datetime.datetime.strptime(datetime_str,
                                                            datetime_format)
                        timestamps.add(dt_obj)
                    except ValueError:
                        try:
                            dt_obj = datetime.datetime.strptime(datetime_str,
                                                                datetime_format_no_ms)
                            timestamps.add(dt_obj)
                        except ValueError:
                            print(f"Err: cannot parse dt '{datetime_str}' in {filepath}.") # Max shorten
                            print(f"Row: {row}")
                            return None
    except Exception as e:
        print(f"Error reading CSV file '{filepath}': {e}")
        return None
    return timestamps


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Check CSV time consistency.") # Max shorten
    parser.add_argument("input_dir", help="Dir with CSVs.")
    args: argparse.Namespace = parser.parse_args() # Assuming this line is fine

    input_directory: str = args.input_dir

    if not os.path.exists(input_directory):
        print(f"Error: Dir '{input_directory}' not found.")
        exit(1)  #  Exit with error code

    csv_files: List[str] = [
        f for f in os.listdir(input_directory) if f.endswith('.csv')
    ]

    if not csv_files:
        print(f"Error: No CSVs found in '{input_directory}'.")  # Shortened
        exit(1)  # Exit with error code

    reference_timestamps: Optional[Set[datetime.datetime]] = None
    first_filename: str = ""

    print("Checking timestamps in CSV files...")

    for i, filename in enumerate(csv_files):
        filepath: str = os.path.join(input_directory, filename)
        current_timestamps: Optional[Set[datetime.datetime]] = \
            get_timestamps_from_csv(filepath)

        if current_timestamps is None:
            print(f"Skipping comparison for '{filename}' due to errors.")
            continue

        if reference_timestamps is None:
            reference_timestamps = current_timestamps
            first_filename = filename
            print(f"Using timestamps from '{first_filename}' as reference.")
        else:
            if current_timestamps == reference_timestamps:
                print(f"Timestamps in '{filename}' match the reference.")
            else:
                missing_ts: Set[datetime.datetime] = \
                    reference_timestamps - current_timestamps
                extra_ts: Set[datetime.datetime] = \
                    current_timestamps - reference_timestamps

                if missing_ts:
                    # Line too long, break f-string
                    print(f"Error: '{filename}' is missing "
                          f"{len(missing_ts)} timestamps compared to "
                          f"'{first_filename}'.")
                    for ts_obj in sorted(list(missing_ts))[:5]:
                        print(f"  Missing: {ts_obj}")
                    if len(missing_ts) > 5:
                        print("  ...and more")
                if extra_ts:
                    # Line too long, break f-string
                    print(f"Error: '{filename}' has {len(extra_ts)} "
                          f"extra timestamps compared to '{first_filename}'.")
                    for ts_obj in sorted(list(extra_ts))[:5]:
                        print(f"  Extra: {ts_obj}")
                    if len(extra_ts) > 5:
                        print("  ...and more")

                if not missing_ts and not extra_ts:
                    # This block handles cases where timestamp counts are
                    # the same, but contents differ.
                    ref_list: List[datetime.datetime] = \
                        sorted(list(reference_timestamps))
                    cur_list: List[datetime.datetime] = \
                        sorted(list(current_timestamps))
                    diff_count: int = 0
                    for j in range(min(len(ref_list), len(cur_list))):
                        if ref_list[j] != cur_list[j]:
                            diff_count += 1
                    if diff_count > 0:
                        # Line too long, break f-string
                        print(f"Error: '{filename}' has {diff_count} "
                              f"different timestamps at the same positions "
                              f"compared to '{first_filename}'.")
                        for j in range(min(len(ref_list), len(cur_list))):
                            if ref_list[j] != cur_list[j]:
                                # Line too long, break f-string
                                print(f"  Different at pos {j+1}: "
                                      f"Ref: {ref_list[j]}, "
                                      f"Cur: {cur_list[j]}")
                                if diff_count >= 5 and j >= 4:
                                    print("  ...and more")
                                    break
    print("\nTimestamp check complete.")
