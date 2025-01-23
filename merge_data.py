import csv
import os
import datetime
import argparse # For command-line arguments

def merge_csv_files_to_one(input_dir, output_filepath):
    """
    Merges multiple CSV files from input_dir into a single CSV file.
    """
    merged_data = {}
    country_codes_header = []
    datetime_format_input = '%Y-%m-%d %H:%M:%S.%f' # Input format with milliseconds
    datetime_format_input_no_ms = '%Y-%m-%d %H:%M:%S' # Input format without milliseconds

    csv_files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]

    if not csv_files:
        print(f"Error: No CSV files found in '{input_dir}'.")
        return

    for filename in csv_files:
        country_code = filename[:-4]
        filepath = os.path.join(input_dir, filename)
        country_codes_header.append(country_code)

        with open(filepath, 'r', encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile)
            next(csv_reader, None) # Skip header

            for row in csv_reader:
                if row:
                    datetime_str = row[0]
                    value = row[1]
                    try:
                        datetime_obj = datetime.datetime.strptime(datetime_str, datetime_format_input)
                    except ValueError:
                        datetime_obj = datetime.datetime.strptime(datetime_str, datetime_format_input_no_ms)

                    datetime_str_key = datetime_obj.strftime(datetime_format_input)

                    if datetime_str_key not in merged_data:
                        merged_data[datetime_str_key] = {}
                    merged_data[datetime_str_key][country_code] = value

    sorted_timestamps = sorted(merged_data.keys())
    sorted_country_codes_header = sorted(country_codes_header)

    try:
        with open(output_filepath, 'w', newline='', encoding='utf-8') as outfile:
            csv_writer = csv.writer(outfile)
            header_row = ['date and time'] + sorted_country_codes_header
            csv_writer.writerow(header_row)

            for timestamp in sorted_timestamps:
                row = [timestamp]
                for country_code in sorted_country_codes_header:
                    value = merged_data[timestamp].get(country_code, 'NA')
                    row.append(value)
                csv_writer.writerow(row)

        print(f"Merged data saved to '{output_filepath}'")

    except Exception as e:
        print(f"Error writing merged CSV file: {e}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Merge CSV files from a directory into a single CSV.")
    parser.add_argument("input_dir", help="Path to the directory containing CSV files to merge.")
    parser.add_argument("output_file", help="Path to save the merged CSV file.")
    args = parser.parse_args()

    input_directory = args.input_dir
    output_file = args.output_file

    merge_csv_files_to_one(input_directory, output_file)
    print("Merging process complete.")