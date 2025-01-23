import csv
import os
import datetime
import argparse  # For command-line arguments

def get_timestamps_from_csv(filepath):
    """
    Extracts timestamps from the 'date and time' column of a CSV file.
    """
    timestamps = set()
    try:
        with open(filepath, 'r', encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile)
            header = next(csv_reader, None)
            if header is None:
                print(f"Warning: CSV file '{filepath}' is empty.")
                return None
            if 'date and time' not in header:
                print(f"Warning: 'date and time' column not found in '{filepath}'. Header: {header}")
                return None

            datetime_format = '%Y-%m-%d %H:%M:%S.%f' # Format with milliseconds
            datetime_format_no_ms = '%Y-%m-%d %H:%M:%S' # Format without milliseconds

            for row in csv_reader:
                if row:
                    datetime_str = row[0]
                    try:
                        datetime_obj = datetime.datetime.strptime(datetime_str, datetime_format)
                        timestamps.add(datetime_obj)
                    except ValueError:
                        try:
                            datetime_obj = datetime.datetime.strptime(datetime_str, datetime_format_no_ms)
                            timestamps.add(datetime_obj)
                        except ValueError:
                            print(f"Error: Could not parse datetime '{datetime_str}' in '{filepath}'. Row: {row}")
                            return None

    except Exception as e:
        print(f"Error reading CSV file '{filepath}': {e}")
        return None
    return timestamps

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Check timestamp consistency across CSV files in a directory.")
    parser.add_argument("input_dir", help="Path to the directory containing CSV files.")
    args = parser.parse_args()

    input_directory = args.input_dir

    if not os.path.exists(input_directory):
        print(f"Error: Directory '{input_directory}' not found.")
        exit(1) # Exit with error code

    csv_files = [f for f in os.listdir(input_directory) if f.endswith('.csv')]

    if not csv_files:
        print(f"Error: No CSV files found in '{input_directory}'.")
        exit(1) # Exit with error code

    reference_timestamps = None
    first_filename = ""

    print("Checking timestamps in CSV files...")

    for i, filename in enumerate(csv_files):
        filepath = os.path.join(input_directory, filename)
        current_timestamps = get_timestamps_from_csv(filepath)

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
                missing_timestamps = reference_timestamps - current_timestamps
                extra_timestamps = current_timestamps - reference_timestamps
                if missing_timestamps:
                    print(f"Error: '{filename}' is missing {len(missing_timestamps)} timestamps compared to '{first_filename}'.")
                    for ts in sorted(list(missing_timestamps))[:5]:
                        print(f"  Missing: {ts}")
                    if len(missing_timestamps) > 5:
                        print("  ...and more")
                if extra_timestamps:
                    print(f"Error: '{filename}' has {len(extra_timestamps)} extra timestamps compared to '{first_filename}'.")
                    for ts in sorted(list(extra_timestamps))[:5]:
                        print(f"  Extra: {ts}")
                    if len(extra_timestamps) > 5:
                        print("  ...and more")
                if not missing_timestamps and not extra_timestamps:
                    reference_list = sorted(list(reference_timestamps))
                    current_list = sorted(list(current_timestamps))
                    different_timestamps_count = 0
                    for j in range(min(len(reference_list), len(current_list))):
                        if reference_list[j] != current_list[j]:
                            different_timestamps_count += 1
                    if different_timestamps_count > 0:
                        print(f"Error: '{filename}' has {different_timestamps_count} different timestamps at the same positions compared to '{first_filename}'.")
                        for j in range(min(len(reference_list), len(current_list))):
                            if reference_list[j] != current_list[j]:
                                print(f"  Different at position {j+1}: Reference: {reference_list[j]}, Current: {current_list[j]}")
                                if different_timestamps_count >= 5 and j >= 4:
                                    print("  ...and more")
                                    break

    print("\nTimestamp check complete.")
