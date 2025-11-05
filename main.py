"""
Google Transparency Report YouTube Traffic Data Downloader.

This script downloads YouTube traffic data from Google's Transparency Report API
for multiple countries over a specified time period.
"""

import argparse
import csv
import datetime
import json
import logging
import os
import time
from typing import Optional, List, Dict, Any
from pathlib import Path

import requests
from tqdm import tqdm

from utils import (
    timestamp_to_datetime,
    datetime_to_timestamp,
    format_datetime,
    extract_data_points,
    setup_logging,
    get_month_boundaries,
    validate_country_code,
    API_BASE_URL,
    API_SECURITY_PREFIX,
    YOUTUBE_PRODUCT_ID
)


logger = logging.getLogger(__name__)


class DownloadStats:
    """Tracks download statistics and failures."""

    def __init__(self):
        self.successful_countries = 0
        self.failed_countries = 0
        self.total_data_points = 0
        self.failures: List[Dict[str, str]] = []

    def add_success(self, country_code: str, data_points: int) -> None:
        """Record a successful download."""
        self.successful_countries += 1
        self.total_data_points += data_points

    def add_failure(self, country_code: str, reason: str) -> None:
        """Record a failed download."""
        self.failed_countries += 1
        self.failures.append({'country': country_code, 'reason': reason})

    def print_summary(self) -> None:
        """Print download statistics summary."""
        logger.info("=" * 60)
        logger.info("Download Summary:")
        logger.info(f"  Successful countries: {self.successful_countries}")
        logger.info(f"  Failed countries: {self.failed_countries}")
        logger.info(f"  Total data points: {self.total_data_points}")

        if self.failures:
            logger.warning(f"\nFailed downloads ({len(self.failures)}):")
            for failure in self.failures[:10]:  # Show first 10
                logger.warning(f"  - {failure['country']}: {failure['reason']}")
            if len(self.failures) > 10:
                logger.warning(f"  ... and {len(self.failures) - 10} more")
        logger.info("=" * 60)


def download_traffic_data(
    region_code: str,
    start_timestamp_ms: int,
    end_timestamp_ms: int,
    max_retries: int = 3,
    retry_delay: float = 2.0
) -> Optional[List[Dict[str, Any]]]:
    """
    Downloads YouTube traffic data from Google Transparency Report API.

    Args:
        region_code: ISO 3166-1 alpha-2 region code (e.g., "US", "RU").
        start_timestamp_ms: Start timestamp in milliseconds.
        end_timestamp_ms: End timestamp in milliseconds.
        max_retries: Maximum number of retry attempts.
        retry_delay: Initial delay between retries in seconds (exponential backoff).

    Returns:
        List of data points if successful, None if download fails.
    """
    params = {
        "start": start_timestamp_ms,
        "end": end_timestamp_ms,
        "region": region_code,
        "product": YOUTUBE_PRODUCT_ID
    }

    for attempt in range(max_retries):
        try:
            response = requests.get(API_BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            content = response.text

            # Remove security prefix if present
            if content.startswith(API_SECURITY_PREFIX):
                content = content[len(API_SECURITY_PREFIX):]

            if not content.strip():
                logger.warning(f"Empty response for {region_code}")
                return None

            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error for {region_code}: {e}")
                save_error_response(region_code, content)
                return None

            # Extract data points using utility function
            data_points = extract_data_points(data)

            if not data_points:
                logger.warning(f"No data points extracted for {region_code}")

            return data_points

        except requests.exceptions.Timeout:
            logger.warning(f"Timeout for {region_code} (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                continue
            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {region_code}: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (2 ** attempt))
                continue
            return None

        except Exception as e:
            logger.error(f"Unexpected error for {region_code}: {e}")
            return None

    return None


def save_error_response(region_code: str, content: str, error_dir: str = "error_responses_monthly") -> None:
    """
    Saves error response content to a file for debugging.

    Args:
        region_code: Country code.
        content: Response content to save.
        error_dir: Directory to save error responses.
    """
    os.makedirs(error_dir, exist_ok=True)
    error_path = os.path.join(error_dir, f"{region_code}_error_response.txt")

    try:
        with open(error_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.debug(f"Error response saved to {error_path}")
    except Exception as e:
        logger.error(f"Failed to save error response for {region_code}: {e}")


def save_to_csv(
    region_code: str,
    data_points: List[Dict[str, Any]],
    output_dir: str = "."
) -> bool:
    """
    Saves traffic data to a CSV file.

    Args:
        region_code: ISO 3166-1 alpha-2 region code.
        data_points: List of data points to save.
        output_dir: Directory where the CSV file will be saved.

    Returns:
        True if save was successful, False otherwise.
    """
    if not data_points:
        logger.warning(f"No data to save for {region_code}")
        return False

    filepath = os.path.join(output_dir, f"{region_code}.csv")

    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(['date and time', 'value'])

            for point in data_points:
                datetime_obj = timestamp_to_datetime(point['timestamp_ms'])
                datetime_str = format_datetime(datetime_obj, include_ms=True)
                csv_writer.writerow([datetime_str, point['value']])

        logger.info(f"Saved {len(data_points)} data points for {region_code}")
        return True

    except Exception as e:
        logger.error(f"Error saving CSV for {region_code}: {e}")
        return False


def load_country_codes(filepath: Optional[str] = None) -> List[str]:
    """
    Loads country codes from a file or returns default list.

    Args:
        filepath: Optional path to file containing country codes.

    Returns:
        List of country codes.
    """
    if filepath and os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                codes = [line.strip().upper() for line in f if line.strip()]
                codes = [code for code in codes if validate_country_code(code)]
                logger.info(f"Loaded {len(codes)} country codes from {filepath}")
                return codes
        except Exception as e:
            logger.error(f"Error loading country codes from {filepath}: {e}")

    # Default country codes
    default_codes = ["OM", "MV", "BJ", "NZ", "MD", "AW", "CN", "EE", "HR", "AE", "SL", "FI", "BI", "VG", "GM", "ID", "YT", "TR", "VI", "AX", "CO", "MW", "LA", "FJ", "ME", "KN", "PR", "GN", "IE", "LR", "NI", "AF", "AU", "US", "CL", "EC", "ZW", "UA", "BY", "IT", "ET", "VE", "NF", "MS", "QA", "BG", "TN", "RW", "MU", "MC", "CM", "NG", "AD", "SK", "BZ", "MT", "BH", "TO", "GL", "VU", "KI", "IR", "PM", "BW", "SH", "MQ", "KZ", "TL", "BE", "RU", "GI", "VC", "PL", "AR", "SY", "CI", "MA", "AT", "CK", "RE", "NE", "SI", "DO", "IS", "BF", "ES", "TM", "SZ", "HN", "JE", "MR", "LK", "GY", "TJ", "RS", "CY", "GG", "CG", "HK", "MO", "DK", "SG", "DM", "IQ", "KH", "CZ", "GH", "NC", "KY", "MP", "BD", "KG", "ZA", "PK", "CH", "TH", "BA", "GE", "LI", "FR", "MM", "IM", "PH", "SC", "BR", "GF", "NA", "SE", "BT", "KW", "MN", "BB", "NR", "AO", "CF", "SV", "TZ", "BS", "SD", "DJ", "KE", "IN", "MK", "CU", "RO", "PF", "NO", "AL", "SA", "VN", "TW", "GT", "PW", "GB", "JO", "ML", "PY", "CV", "TG", "GD", "AM", "PG", "CD", "ST", "DZ", "SB", "GU", "IL", "NP", "LY", "WS", "JP", "CA", "BN", "DE", "GR", "LV", "UY", "CR", "TC", "JM", "MZ", "MH", "SR", "FO", "ZM", "PE", "BO", "TV", "KR", "TD", "UZ", "GA", "GP", "LT", "YE", "HT", "LB", "MX", "PS", "EG", "LS", "PA", "AG", "SN", "NL", "LU", "AI", "UG", "MY", "LC", "BM", "TT", "GQ", "PT", "AZ", "HU", "SO", "MG"]
    logger.info(f"Using default list of {len(default_codes)} country codes")
    return default_codes


def parse_arguments() -> argparse.Namespace:
    """
    Parses command-line arguments.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Download YouTube traffic data from Google Transparency Report API",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        '--start-date',
        type=str,
        default='2019-01-01',
        help='Start date in YYYY-MM-DD format'
    )

    parser.add_argument(
        '--end-date',
        type=str,
        default=datetime.date.today().isoformat(),
        help='End date in YYYY-MM-DD format'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='youtube_traffic_data_monthly',
        help='Output directory for CSV files'
    )

    parser.add_argument(
        '--error-dir',
        type=str,
        default='error_responses_monthly',
        help='Directory for error responses'
    )

    parser.add_argument(
        '--countries-file',
        type=str,
        default=None,
        help='Path to file containing country codes (one per line)'
    )

    parser.add_argument(
        '--delay',
        type=float,
        default=0.5,
        help='Delay between API requests in seconds'
    )

    parser.add_argument(
        '--max-retries',
        type=int,
        default=3,
        help='Maximum number of retries for failed requests'
    )

    parser.add_argument(
        '--log-file',
        type=str,
        default=None,
        help='Path to log file (logs to console if not specified)'
    )

    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level'
    )

    return parser.parse_args()


def main() -> None:
    """Main execution function."""
    args = parse_arguments()

    # Setup logging
    log_level = getattr(logging, args.log_level)
    setup_logging(level=log_level, log_file=args.log_file)

    logger.info("Starting YouTube traffic data download")
    logger.info(f"Date range: {args.start_date} to {args.end_date}")

    # Parse dates
    try:
        start_date = datetime.datetime.strptime(args.start_date, '%Y-%m-%d')
        end_date = datetime.datetime.strptime(args.end_date, '%Y-%m-%d').replace(
            hour=23, minute=59, second=59
        )
    except ValueError as e:
        logger.error(f"Invalid date format: {e}")
        return

    # Create output directories
    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(args.error_dir, exist_ok=True)

    # Load country codes
    country_codes = load_country_codes(args.countries_file)

    if not country_codes:
        logger.error("No valid country codes found")
        return

    # Calculate month boundaries
    month_boundaries = get_month_boundaries(start_date, end_date)
    total_requests = len(country_codes) * len(month_boundaries)

    logger.info(f"Processing {len(country_codes)} countries across {len(month_boundaries)} months")
    logger.info(f"Total API requests: {total_requests}")

    # Initialize statistics
    stats = DownloadStats()
    start_time = time.time()

    # Progress bar
    with tqdm(total=total_requests, desc="Downloading") as pbar:
        for country_code in country_codes:
            all_data_points = []
            country_failed = False

            for month_start, month_end in month_boundaries:
                start_ts = datetime_to_timestamp(month_start)
                end_ts = datetime_to_timestamp(month_end)

                pbar.set_description(f"Downloading {country_code} ({month_start.strftime('%Y-%m')})")

                monthly_data = download_traffic_data(
                    country_code,
                    start_ts,
                    end_ts,
                    max_retries=args.max_retries
                )

                if monthly_data:
                    all_data_points.extend(monthly_data)
                else:
                    country_failed = True

                pbar.update(1)
                time.sleep(args.delay)

            # Save country data
            if all_data_points:
                if save_to_csv(country_code, all_data_points, args.output_dir):
                    stats.add_success(country_code, len(all_data_points))
                else:
                    stats.add_failure(country_code, "Failed to save CSV")
            else:
                reason = "No data downloaded" if country_failed else "Empty response"
                stats.add_failure(country_code, reason)
                logger.warning(f"No data for {country_code}")

    # Print summary
    elapsed_time = time.time() - start_time
    logger.info(f"Total execution time: {datetime.timedelta(seconds=int(elapsed_time))}")
    stats.print_summary()

    logger.info("Download process complete")


if __name__ == '__main__':
    main()
