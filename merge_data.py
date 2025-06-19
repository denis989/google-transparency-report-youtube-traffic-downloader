"""
Merges multiple country-specific CSV files into a single consolidated CSV file.

This script takes an input directory containing individual CSV files (one per
country, named as {country_code}.csv) and an output file path. It combines
the data from all input CSVs, aligning them by timestamp. The resulting
merged CSV will have a 'date and time' column followed by columns for each
country code, with 'NA' representing missing values.
"""
import csv
import os
import datetime
import argparse
from typing import Dict, List, Optional, Iterator  # Removed Any


def merge_csv_files_to_one(input_dir: str, output_filepath: str) -> None:
    """
    Merges CSVs from input_dir into output_filepath.

    Input CSVs should be {country_code}.csv with 'date and time', 'value'.
    Merged file aligns timestamps, sorts country columns, uses 'NA' for missing.

    Args:
        input_dir: Path to directory with individual CSV files.
        output_filepath: Path to save the merged CSV.

    Side effects:
        Prints status/errors. Creates/overwrites output CSV.
    """
    merged_data: Dict[str, Dict[str, str]] = {}
    country_codes_header: List[str] = []
    # Input format with milliseconds
    datetime_fmt_ms: str = '%Y-%m-%d %H:%M:%S.%f'  # Ensure space for E261
    # Input format without milliseconds
    datetime_fmt_no_ms: str = '%Y-%m-%d %H:%M:%S'  # Ensure space for E261

    csv_files: List[str] = [
        f for f in os.listdir(input_dir) if f.endswith('.csv')
    ]

    if not csv_files:
        print(f"Error: No CSV files found in '{input_dir}'.")
        return

    for filename in csv_files:
        country_code: str = filename[:-4]  # Remove .csv
        filepath: str = os.path.join(input_dir, filename)
        country_codes_header.append(country_code)

        try:
            with open(filepath, 'r', encoding='utf-8') as csvfile:
                csv_reader: Iterator[List[str]] = csv.reader(csvfile)
                next(csv_reader, None)  # Skip header

                for row_data in csv_reader:
                    if row_data and len(row_data) >= 2:
                        datetime_str: str = row_data[0]
                        value: str = row_data[1]
                        datetime_obj: Optional[datetime.datetime] = None
                        try:
                            datetime_obj = datetime.datetime.strptime(
                                datetime_str, datetime_fmt_ms
                            )
                        except ValueError:
                            try:
                                datetime_obj = datetime.datetime.strptime(
                                    datetime_str, datetime_fmt_no_ms
                                )
                            except ValueError:
                                msg = (f"Warn: date parse err '{datetime_str}' "
                                       f"in {filename}. Skip row.")
                                print(msg)
                                continue  # Skip row

                        if datetime_obj:
                            # Standardize key format
                            dt_key: str = datetime_obj.strftime(datetime_fmt_ms)
                            if dt_key not in merged_data:
                                merged_data[dt_key] = {}
                            merged_data[dt_key][country_code] = value
        except IOError as e:
            print(f"ERR reading '{filepath}': {e}. Skip.")  # Max shorten E501 L71
            country_codes_header.pop()  # Remove country if file error
            continue  # Skip to next file

    if not merged_data:
        print("No data from CSVs. Output not made.")  # Max shorten E501 L78
        return

    sorted_timestamps: List[str] = sorted(merged_data.keys())
    sorted_codes: List[str] = sorted(country_codes_header)  # Renamed var

    try:
        with open(output_filepath, 'w', newline='', encoding='utf-8') as outfile:
            csv_writer = csv.writer(outfile)
            header: List[str] = ['date and time'] + sorted_codes  # Use renamed
            csv_writer.writerow(header)

            for ts_key in sorted_timestamps:  # Renamed var
                row_to_write: List[str] = [ts_key]
                for cc_hdr in sorted_codes:  # Renamed var
                    val_out = merged_data[ts_key].get(cc_hdr, 'NA')
                    row_to_write.append(val_out)
                csv_writer.writerow(row_to_write)

        print(f"Merged data saved: '{output_filepath}'")  # Max shorten E501 L95

    except IOError as e:  # More specific for file writing
        print(f"IOERR writing merged CSV '{output_filepath}': {e}")
    except Exception as e:  # Catch other unexpected errors
        print(f"Unexpected ERR during CSV write: {e}")


if __name__ == '__main__':
    desc_main = "Merge CSVs into a single CSV file."  # Max shorten E501 L62
    parser = argparse.ArgumentParser(description=desc_main)
    parser.add_argument(
        "input_dir",
        help="Path to the directory containing CSV files to merge."
    )
    parser.add_argument(
        "output_file",
        help="Path to save the merged CSV file."
    )
    args: argparse.Namespace = parser.parse_args()

    input_directory: str = args.input_dir
    output_file: str = args.output_file

    merge_csv_files_to_one(input_directory, output_file)
    print("Merging process complete.")
