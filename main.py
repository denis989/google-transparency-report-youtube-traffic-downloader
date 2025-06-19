"""
Main script to download YouTube traffic data from Google Transparency Report.

This script fetches data for specified countries and date ranges,
handles API interactions including retries, parses the data,
and saves it to CSV files. It uses command-line arguments for configuration.
"""
import argparse
import datetime
import json
import logging
import os
import time
import csv
from typing import (List, Optional, Dict, Any,  # Formatted for line length
                    Union)

import requests
from tqdm import tqdm


def timestamp_to_datetime(timestamp_ms: int) -> datetime.datetime:
    """
    Converts a timestamp in milliseconds to a datetime.datetime object.

    Args:
        timestamp_ms: Timestamp in milliseconds.

    Returns:
        A datetime.datetime object corresponding to the given timestamp.
    """
    return datetime.datetime.fromtimestamp(timestamp_ms / 1000)


def valid_date(s: str) -> datetime.datetime:
    """
    Helper function to validate date string format for argparse.

    Args:
        s: Date string from command-line argument.

    Returns:
        A datetime.datetime object if the string is a valid date.

    Raises:
        argparse.ArgumentTypeError: If the string is not a valid date
                                    in YYYY-MM-DD format.
    """
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = f"Not a valid date: '{s}'. Expected format YYYY-MM-DD."
        raise argparse.ArgumentTypeError(msg)


class GoogleTransparencyAPI:
    """
    Encapsulates interactions with the Google Transparency Report API.

    This class handles downloading YouTube traffic data, including retry
    mechanisms and error handling for API requests.
    """
    def __init__(self) -> None:
        """
        Initializes the API client.

        Sets the base URL for the Google Transparency Report API and the
        product ID for YouTube traffic.
        """
        self.base_url: str = (
            "https://transparencyreport.google.com/transparencyreport/api/v3/"
            "traffic/fraction"  # Line broken for length
        )
        self.product_id: int = 21  # Product ID for YouTube traffic

    def download_traffic_data(
        self,
        region_code: str,
        start_timestamp_ms: int,
        end_timestamp_ms: int
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Downloads YouTube traffic data for a specific region and time range.

        Handles API request retries and common errors like HTTP issues or
        JSON parsing problems.

        Args:
            region_code: The ISO 3166-1 alpha-2 country code.
            start_timestamp_ms: The start of the data range as a Unix
                                timestamp in milliseconds.
            end_timestamp_ms: The end of the data range as a Unix
                              timestamp in milliseconds.

        Returns:
            A list of data point dictionaries, where each dictionary contains
            'timestamp_ms' (int) and 'value' (float or int representing the
            traffic fraction). Returns None if the download fails after retries
            or if critical parsing errors occur.
        """
        params: Dict[str, Union[int, str]] = {
            "start": start_timestamp_ms,
            "end": end_timestamp_ms,
            "region": region_code,
            "product": self.product_id
        }
        max_retries: int = 3
        retry_delay_seconds: int = 1  # Correctly indented

        for attempt in range(max_retries):  # Correctly indented
            try:
                response = requests.get(
                    self.base_url, params=params, timeout=30
                )
                response.raise_for_status()  # Raise HTTPError for bad responses
                content: str = response.text

                if content.startswith(")]}'\n"):  # Remove XSSI prefix
                    content = content[5:]

                if not content.strip():  # Check for empty response
                    logging.warning(f"Empty response: {region_code} A{attempt+1}") # Max shorten
                    return None

                try:
                    # Type for 'data' can be complex, using Any for now
                    data: Any = json.loads(content)
                except json.JSONDecodeError as e:
                    # Line 122 / 123
                    logging.error(f"JSON error for {region_code}: {e}") # Rephrased
                    # Line 129: E501 - logging.debug can be a bit longer
                    # Breaking this f-string to be safer.
                    logging.debug(
                        f"Raw response for {region_code}:\n"
                        f"{content}"
                    )
                    error_dir: str = "error_responses_monthly"
                    os.makedirs(error_dir, exist_ok=True)
                    # Line 131: E501
                    err_fname_prefix = f"{region_code}_err_att_{attempt+1}"
                    err_fname = (
                        f"{err_fname_prefix}.txt"
                    )
                    error_filename: str = os.path.join(error_dir, err_fname)
                    try:
                        with open(error_filename, 'w', encoding='utf-8') as ef:
                            ef.write(content)
                        # Line 143: E501
                        logging.info(f"Raw rsp {region_code} saved.")
                    except IOError as ioe:
                        # Line 146: E501
                        logging.error(f"IOError saving err_rsp: {ioe}")
                    return None  # No retry for JSON parsing error

                data_points: List[Dict[str, Any]] = []
                # Data structure validation before processing
                # Example path: data[0][1][i][0] for timestamp,
                # data[0][1][i][1][0][1] for value
                if (isinstance(data, list) and data and
                        isinstance(data[0], list) and len(data[0]) > 1 and
                        isinstance(data[0][1], list)):
                    for point_data in data[0][1]:
                        if (isinstance(point_data, list) and
                                len(point_data) >= 2 and
                                isinstance(point_data[1], list) and
                                point_data[1] and
                                isinstance(point_data[1][0], list) and
                                len(point_data[1][0]) >= 2):
                            timestamp_val: int = point_data[0]
                            # Value can be None from API
                            value_val: Optional[Union[int, float]] = (
                                point_data[1][0][1]
                            )
                            if value_val is not None:
                                data_points.append(
                                    {'timestamp_ms': timestamp_val,
                                     'value': value_val}
                                )
                return data_points

            except requests.exceptions.HTTPError as http_err:
                logging.error(
                    f"HTTP error for {region_code} on attempt "
                    f"{attempt + 1}/{max_retries}: "
                    f"{http_err.response.status_code} - {http_err}"
                )
                if attempt + 1 == max_retries:
                    logging.error(
                        f"Final attempt failed for {region_code} "
                        f"due to HTTP error."
                    )
                    return None
                # Retry for server-side errors (5xx)
                if http_err.response.status_code in [500, 502, 503, 504]:
                    logging.info(
                        f"Retrying in {retry_delay_seconds}s "
                        f"for {region_code}..."
                    )
                    time.sleep(retry_delay_seconds)
                    retry_delay_seconds *= 2
                else:  # Client-side errors (4xx), not worth retrying
                    logging.error(
                        f"Client-side HTTP error "
                        f"{http_err.response.status_code} for "
                        f"{region_code}. Not retrying."
                    )
                    return None
            except requests.exceptions.RequestException as req_err:
                # Other network errors (timeout, connection error)
                logging.error(
                    f"Request exception for {region_code} on attempt "
                    f"{attempt + 1}/{max_retries}: {req_err}"
                )
                if attempt + 1 == max_retries:
                    logging.error(
                        f"Final attempt failed for {region_code} "
                        f"due to request exception."
                    )
                    return None
                logging.info(
                    f"Retrying in {retry_delay_seconds}s for {region_code}..."
                )
                time.sleep(retry_delay_seconds)
                retry_delay_seconds *= 2
            except IndexError as e:  # Handle index errors in data structure
                logging.error(
                    f"Error processing data structure for {region_code}: {e}. "
                    "This usually indicates an unexpected API response format."
                )
                # No retry for data structure error
                return None
            # This return should be indented to be part of the for loop's else,
            # or outside the loop if it's the final fallback.
            # Given the logic, it's the fallback after all retries fail.
        return None  # Fallback after all retries are exhausted


def save_to_csv(
    region_code: str,
    data_points: List[Dict[str, Any]],
    output_dir: str = "."
) -> None:
    """
    Saves traffic data to a CSV file in the specified output directory.

    Args:
        region_code: ISO 3166-1 alpha-2 country code.
        data_points: List of data points (dictionaries) to save.
                     Each dictionary should have 'timestamp_ms' and 'value'.
        output_dir: Directory where the CSV file will be saved.
                    Defaults to the current directory.
    """
    if not data_points:  # Check if there is data to save
        logging.info(f"No data to save for {region_code}.")
        return

    filename: str = os.path.join(output_dir, f"{region_code}.csv")
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(['date and time', 'value'])  # Write header row
            for point in data_points:
                datetime_obj = timestamp_to_datetime(point['timestamp_ms'])
                # Format datetime to string with milliseconds
                dt_str = datetime_obj.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                csv_writer.writerow([dt_str, point['value']])
        logging.info(f"Data for {region_code} saved to {filename}")
    except IOError as e:  # Handle file writing errors more specifically
        logging.error(
            f"Error saving CSV file {filename} for {region_code}: {e}"
        )
    except Exception as e:  # Handle other unexpected errors
        logging.error(
            f"An unexpected error occurred while saving CSV "
            f"for {region_code}: {e}"
        )


if __name__ == '__main__':
    # Configure basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()  # Outputs to console by default
        ]
    )

    desc = "Download YouTube traffic data from Google Transparency Report."
    parser = argparse.ArgumentParser(description=desc)
    # Removed extra parenthesis from the line above
    parser.add_argument(
        "--country_codes",
        required=True,
        help="Comma-separated ISO codes (e.g., 'US,CA')."  # Shortened help
    )
    parser.add_argument(
        "--start_date",
        required=True,
        type=valid_date,
        help="Start date for data download (YYYY-MM-DD format)."
    )
    parser.add_argument(  # Break help string for line length
        "--end_date",
        required=True,
        type=valid_date,
        help="End date for data download (YYYY-MM-DD format)."
    )
    args = parser.parse_args()

    # Process country codes from comma-separated string to list of lists
    raw_codes: List[str] = args.country_codes.split(',')
    processed_country_codes: List[List[str]] = [
        [code.strip().upper()] for code in raw_codes if code.strip()
    ]

    # Use parsed dates, adjust end_date to include the whole day
    start_date_dt: datetime.datetime = args.start_date
    end_date_dt: datetime.datetime = args.end_date.replace(
        hour=23, minute=59, second=59
    )

    logging.info(f"Starting data download for countries: {args.country_codes}")
    logging.info(
        f"Period: {start_date_dt.strftime('%Y-%m-%d')} to "
        f"{end_date_dt.strftime('%Y-%m-%d')}"
    )

    api_client = GoogleTransparencyAPI()

    output_dir_main: str = "youtube_traffic_data_monthly"
    error_dir_main: str = "error_responses_monthly"  # For error responses
    os.makedirs(output_dir_main, exist_ok=True)
    os.makedirs(error_dir_main, exist_ok=True)

    # Calculate total units for progress bar more accurately
    num_countries = len(processed_country_codes)
    total_progress_units = 0
    for country_code_info_calc in processed_country_codes:
        current_calc_date = start_date_dt
        while current_calc_date < end_date_dt:
            total_progress_units += 1
            # Move to start of next month for counting
            if current_calc_date.month == 12:
                current_calc_date = current_calc_date.replace(
                    year=current_calc_date.year + 1, month=1, day=1
                )
            else:
                current_calc_date = current_calc_date.replace(
                    month=current_calc_date.month + 1, day=1
                )

    progress_bar = tqdm(total=total_progress_units, desc="Total Progress")
    script_start_time = time.time()

    for country_code_info in processed_country_codes:
        country_code_main: str = country_code_info[0]
        all_country_data: List[Dict[str, Any]] = []
        current_processing_date = start_date_dt

        while current_processing_date < end_date_dt:
            month_start_dt = current_processing_date
            # Calculate end of the current month
            if month_start_dt.month == 12:
                month_end_dt_calc = month_start_dt.replace(
                    year=month_start_dt.year + 1, month=1, day=1
                ) - datetime.timedelta(days=1)
            else:
                month_end_dt_calc = month_start_dt.replace(
                    month=month_start_dt.month + 1, day=1
                ) - datetime.timedelta(days=1)

            # Ensure month_end does not exceed overall period end_date
            month_end_dt = min(month_end_dt_calc, end_date_dt)

            start_ts_ms = int(month_start_dt.timestamp() * 1000)
            end_ts_ms = int(month_end_dt.timestamp() * 1000)

            logging.info(
                f"Downloading data for {country_code_main} "
                f"month: {month_start_dt.strftime('%Y-%m')}"
            )

            monthly_data = api_client.download_traffic_data(
                country_code_main, start_ts_ms, end_ts_ms
            )

            if monthly_data:
                all_country_data.extend(monthly_data)
            else:
                logging.warning(
                    f"No data for {country_code_main} "
                    f"for month {month_start_dt.strftime('%Y-%m')}"
                )

            progress_bar.update(1)

            # Move to the start of the next month
            current_processing_date = month_end_dt + datetime.timedelta(days=1)
            time.sleep(0.5)  # API kindness delay

        logging.info(f"Downloading for {country_code_main} complete.")
        if all_country_data:
            save_to_csv(country_code_main, all_country_data, output_dir_main)
        else:
            logging.warning(
                f"No data for {country_code_main} for the entire period."
            )

    progress_bar.close()
    logging.info("Download and save process complete.")
