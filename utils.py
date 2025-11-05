"""
Shared utilities module for Google Transparency Report YouTube Traffic Downloader.

This module contains common functions and constants used across multiple scripts.
"""

import datetime
from typing import Optional, Set, Any
import logging

# Constants
DATETIME_FORMAT_WITH_MS = '%Y-%m-%d %H:%M:%S.%f'
DATETIME_FORMAT_NO_MS = '%Y-%m-%d %H:%M:%S'
YOUTUBE_PRODUCT_ID = 21
API_BASE_URL = "https://transparencyreport.google.com/transparencyreport/api/v3/traffic/fraction"
API_SECURITY_PREFIX = ")]}'\n"


def timestamp_to_datetime(timestamp_ms: int) -> datetime.datetime:
    """
    Converts a timestamp in milliseconds to a datetime object.

    Args:
        timestamp_ms: Timestamp in milliseconds.

    Returns:
        Datetime object corresponding to the timestamp.
    """
    return datetime.datetime.fromtimestamp(timestamp_ms / 1000)


def datetime_to_timestamp(dt: datetime.datetime) -> int:
    """
    Converts a datetime object to a timestamp in milliseconds.

    Args:
        dt: Datetime object to convert.

    Returns:
        Timestamp in milliseconds.
    """
    return int(dt.timestamp() * 1000)


def parse_datetime_string(datetime_str: str) -> Optional[datetime.datetime]:
    """
    Parses a datetime string with support for both millisecond and non-millisecond formats.

    Args:
        datetime_str: String representation of a datetime.

    Returns:
        Datetime object if parsing is successful, None otherwise.
    """
    try:
        return datetime.datetime.strptime(datetime_str, DATETIME_FORMAT_WITH_MS)
    except ValueError:
        try:
            return datetime.datetime.strptime(datetime_str, DATETIME_FORMAT_NO_MS)
        except ValueError:
            logging.error(f"Could not parse datetime string: {datetime_str}")
            return None


def format_datetime(dt: datetime.datetime, include_ms: bool = True) -> str:
    """
    Formats a datetime object to a string.

    Args:
        dt: Datetime object to format.
        include_ms: Whether to include milliseconds in the output.

    Returns:
        Formatted datetime string.
    """
    if include_ms:
        return dt.strftime(DATETIME_FORMAT_WITH_MS)[:-3]  # Truncate to 3 decimal places
    return dt.strftime(DATETIME_FORMAT_NO_MS)


def validate_api_response_structure(data: Any) -> bool:
    """
    Validates the structure of the API response data.

    Args:
        data: The parsed JSON response from the API.

    Returns:
        True if the structure is valid, False otherwise.
    """
    if not isinstance(data, list):
        return False

    if not data or not isinstance(data[0], list):
        return False

    if len(data[0]) <= 1 or not isinstance(data[0][1], list):
        return False

    return True


def extract_data_points(data: Any) -> list[dict[str, Any]]:
    """
    Extracts data points from the API response structure.

    Args:
        data: The parsed JSON response from the API.

    Returns:
        List of data points with timestamp_ms and value keys.
    """
    data_points = []

    if not validate_api_response_structure(data):
        logging.warning("Invalid API response structure")
        return data_points

    try:
        for point in data[0][1]:
            if not isinstance(point, list) or len(point) < 2:
                continue

            if not isinstance(point[1], list) or not point[1]:
                continue

            if not isinstance(point[1][0], list) or len(point[1][0]) < 2:
                continue

            timestamp_ms = point[0]
            value = point[1][0][1]

            if value is not None:
                data_points.append({
                    'timestamp_ms': timestamp_ms,
                    'value': value
                })
    except (IndexError, TypeError) as e:
        logging.error(f"Error extracting data points: {e}")

    return data_points


def setup_logging(level: int = logging.INFO, log_file: Optional[str] = None) -> None:
    """
    Configures logging for the application.

    Args:
        level: Logging level (default: INFO).
        log_file: Optional path to a log file.
    """
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=handlers
    )


def get_month_boundaries(start_date: datetime.datetime, end_date: datetime.datetime) -> list[tuple[datetime.datetime, datetime.datetime]]:
    """
    Generates a list of month boundary pairs between start and end dates.

    Args:
        start_date: Starting date for the period.
        end_date: Ending date for the period.

    Returns:
        List of tuples containing (month_start, month_end) datetime pairs.
    """
    boundaries = []
    current_date = start_date

    while current_date < end_date:
        month_start = current_date
        # Calculate end of month
        next_month = current_date.replace(day=28) + datetime.timedelta(days=4)
        month_end = next_month.replace(day=1) - datetime.timedelta(days=1)

        # Cap at overall end date
        if month_end > end_date:
            month_end = end_date

        boundaries.append((month_start, month_end))
        current_date = month_end + datetime.timedelta(days=1)

    return boundaries


def validate_country_code(code: str) -> bool:
    """
    Validates if a country code is in the correct format (2 uppercase letters).

    Args:
        code: Country code to validate.

    Returns:
        True if valid, False otherwise.
    """
    return isinstance(code, str) and len(code) == 2 and code.isupper() and code.isalpha()
