# Google Transparency Report YouTube Traffic Downloader and Merger

## Project Overview

This project provides Python scripts to automatically download YouTube traffic data from the Google Transparency Report API and merge it into a single CSV file for analysis. The scripts are designed to:

1.  **Download YouTube Traffic Data:**  Fetch traffic fraction data for multiple countries over a specified time period from the Google Transparency Report API.
2.  **Ensure Data Consistency:** Check if downloaded CSV files have consistent timestamps, which is crucial for merging data correctly.
3.  **Merge Data into a Single File:** Combine data from individual country CSV files into one consolidated CSV file, making it easier to analyze and compare traffic trends across different regions.

This project is useful for researchers, analysts, or anyone interested in studying global YouTube traffic patterns as reported by Google's Transparency Report.

## Features

- **Fully Configurable:** CLI arguments for dates, directories, retry logic, and logging
- **Robust Error Handling:** Automatic retry with exponential backoff for failed requests
- **Professional Logging:** Structured logging with configurable levels (DEBUG, INFO, WARNING, ERROR)
- **Statistics Tracking:** Comprehensive summaries of downloads, merges, and failures
- **Type Safety:** Full type hints for better IDE support and code clarity
- **Modular Design:** Shared utilities module eliminates code duplication
- **Production Ready:** Proper dependency management and error recovery

## Installation

1.  **Python:** Ensure you have Python 3.8+ installed on your system.

2.  **Install Dependencies:** Install the required Python libraries using pip:
    ```bash
    pip install -r requirements.txt
    ```

    This will install:
    - `requests>=2.31.0` - For making HTTP requests to the Google API
    - `tqdm>=4.66.0` - For displaying progress bars

## Quick Start

### 1. Download Data
```bash
# Download data with default settings (2019-01-01 to today)
python main.py

# Download data for a specific date range
python main.py --start-date 2024-01-01 --end-date 2024-12-31

# Download with custom settings
python main.py --start-date 2023-01-01 --end-date 2023-12-31 \
               --output-dir ./data --delay 1.0 --max-retries 5 \
               --log-level INFO
```

### 2. Check Timestamp Consistency
```bash
# Check timestamps in downloaded files
python check_timestamps.py youtube_traffic_data_monthly

# With debug logging
python check_timestamps.py youtube_traffic_data_monthly --log-level DEBUG
```

### 3. Merge Data
```bash
# Merge all country files into one
python merge_data.py youtube_traffic_data_monthly merged_output.csv

# With detailed logging
python merge_data.py youtube_traffic_data_monthly merged_output.csv --log-level INFO
```

## Script Descriptions

### `main.py` - YouTube Traffic Data Downloader

**Purpose:** Downloads YouTube traffic data from the Google Transparency Report API for multiple countries.

**Key Features:**
- Configurable date ranges via CLI arguments
- Automatic retry logic with exponential backoff
- Comprehensive error handling and logging
- Download statistics and failure tracking
- Progress bar with ETA estimation
- Customizable API request delays
- Optional country code file support

**CLI Arguments:**
```
--start-date START_DATE       Start date in YYYY-MM-DD format (default: 2019-01-01)
--end-date END_DATE           End date in YYYY-MM-DD format (default: today)
--output-dir OUTPUT_DIR       Output directory for CSV files (default: youtube_traffic_data_monthly)
--error-dir ERROR_DIR         Directory for error responses (default: error_responses_monthly)
--countries-file FILE         Path to file with country codes (one per line)
--delay SECONDS               Delay between API requests (default: 0.5)
--max-retries N               Maximum retries for failed requests (default: 3)
--log-level LEVEL             Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)
--log-file FILE               Path to log file (logs to console if not specified)
```

**Examples:**
```bash
# Download recent year with custom settings
python main.py --start-date 2024-01-01 --end-date 2024-12-31 \
               --delay 1.0 --max-retries 5

# Download with debug logging to file
python main.py --start-date 2023-01-01 --end-date 2023-12-31 \
               --log-level DEBUG --log-file download.log

# Download specific countries only
echo -e "US\nGB\nDE\nFR" > my_countries.txt
python main.py --countries-file my_countries.txt
```

**Output:**
- Creates CSV files in `youtube_traffic_data_monthly/` (or custom directory)
- Each file named `{country_code}.csv` with columns: `date and time`, `value`
- Saves error responses in `error_responses_monthly/` for debugging
- Displays comprehensive statistics summary at completion

### `check_timestamps.py` - CSV Timestamp Consistency Checker

**Purpose:** Verifies that all CSV files have consistent timestamps for reliable merging.

**Key Features:**
- Validates timestamp consistency across all CSV files
- Detailed reporting of missing or extra timestamps
- Row-level error reporting
- Comprehensive summary statistics
- Configurable logging levels

**CLI Arguments:**
```
input_dir                     Path to directory containing CSV files (required)
--log-level LEVEL             Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)
--log-file FILE               Path to log file (optional)
```

**Examples:**
```bash
# Basic timestamp check
python check_timestamps.py youtube_traffic_data_monthly

# With detailed output
python check_timestamps.py youtube_traffic_data_monthly --log-level DEBUG

# Save check results to file
python check_timestamps.py youtube_traffic_data_monthly --log-file check_results.log
```

**Output:**
- Reports whether all files have consistent timestamps
- Lists any missing, extra, or different timestamps
- Displays summary: total files, files checked, files skipped
- Exit code 0 for success, 1 for errors

### `merge_data.py` - CSV Data Merger

**Purpose:** Merges multiple country-specific CSV files into a single consolidated file.

**Key Features:**
- Merges all country files by timestamp
- Handles missing values with 'NA' placeholder
- Sorts data by timestamp and country code
- Merge statistics and failure tracking
- Configurable logging

**CLI Arguments:**
```
input_dir                     Path to directory with CSV files to merge (required)
output_file                   Path for merged CSV output file (required)
--log-level LEVEL             Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)
--log-file FILE               Path to log file (optional)
```

**Examples:**
```bash
# Basic merge
python merge_data.py youtube_traffic_data_monthly merged_data.csv

# With detailed logging
python merge_data.py youtube_traffic_data_monthly merged_data.csv --log-level INFO

# Save merge log to file
python merge_data.py youtube_traffic_data_monthly merged_data.csv --log-file merge.log
```

**Output:**
- Single CSV file with format: `date and time, AD, AE, AF, ..., ZW`
- One row per timestamp with values for all countries
- Missing values filled with 'NA'
- Displays merge statistics: files processed, total countries, total timestamps

### `utils.py` - Shared Utilities Module

**Purpose:** Common functions and constants used across all scripts.

**Key Components:**
- Timestamp conversion functions
- Datetime parsing with multiple format support
- API response validation and data extraction
- Logging setup and configuration
- Date range calculations
- Country code validation

**Benefits:**
- Eliminates code duplication (~150 lines saved)
- Ensures consistent behavior across scripts
- Easier maintenance and testing
- Centralized configuration

## Algorithm and Data Flow

The project consists of the following main steps:

### 1. Data Download (`main.py`)
1. Parse CLI arguments and setup logging
2. Load country codes (from file or default list)
3. Calculate month boundaries for the date range
4. For each country:
   - For each month:
     - Send API request with retry logic
     - Parse JSON response and extract data points
     - Handle errors and save error responses
   - Save all country data to CSV file
5. Display comprehensive statistics summary

### 2. Timestamp Consistency Check (`check_timestamps.py`)
1. Load all CSV files from input directory
2. Extract timestamps from first file (reference)
3. For each remaining file:
   - Extract timestamps
   - Compare against reference
   - Report any differences
4. Display summary statistics
5. Exit with appropriate status code

### 3. Data Merging (`merge_data.py`)
1. Load all CSV files from input directory
2. Parse each file and build merged data structure
3. Sort timestamps and country codes
4. Write merged CSV with all countries as columns
5. Display merge statistics

## Data Granularity

The Google Transparency Report API provides data with **adaptive granularity** based on the requested time range:

- **Short Time Ranges (1 day, 1 week):** 30-minute granularity
- **Longer Time Ranges (1 month+):** 2-hour granularity (automatic aggregation)
- **API-Controlled:** Granularity cannot be explicitly controlled via parameters

**Granularity in These Scripts:**
- `main.py` downloads data in **month-long windows** → **2-hour granularity**
- For 30-minute granularity, modify the script to download in smaller intervals (daily or weekly)

## Configuration Options

### Environment Variables
None currently required. All configuration via CLI arguments.

### Country Codes
Default: 220+ countries (see `utils.py` or `countries codes.txt`)

**Custom country list file format:**
```
US
GB
DE
FR
JP
```
One ISO 3166-1 alpha-2 country code per line.

### Logging
All scripts support structured logging with levels:
- **DEBUG:** Detailed information for debugging
- **INFO:** General informational messages (default)
- **WARNING:** Warning messages for potential issues
- **ERROR:** Error messages for failures

Logs can be directed to console (default) or file (--log-file option).

## Output Files

### Data Files
- **`youtube_traffic_data_monthly/`**: Country-specific CSV files from `main.py`
  - Format: `{country_code}.csv`
  - Columns: `date and time`, `value`
  - Example: `US.csv`, `GB.csv`

- **Merged CSV** (from `merge_data.py`): Single consolidated file
  - Format: User-specified filename (e.g., `merged_data.csv`)
  - Columns: `date and time`, `AD`, `AE`, `AF`, ..., `ZW`
  - ~25,000+ rows for 6 years of 2-hour granularity data

### Error Files
- **`error_responses_monthly/`**: Raw API error responses from `main.py`
  - Format: `{country_code}_error_response.txt`
  - Contains raw response for debugging

### Log Files
- Optional log files (when using `--log-file` option)
- Structured log messages with timestamps and severity levels

## Error Handling and Recovery

### Automatic Retry Logic
- Failed API requests automatically retry up to N times (default: 3)
- Exponential backoff: 2s, 4s, 8s delays between retries
- Configurable via `--max-retries` argument

### Error Types Handled
- **Network timeouts:** Automatic retry with exponential backoff
- **HTTP errors:** Logged with status codes and retry
- **JSON parsing errors:** Raw response saved to error directory
- **File I/O errors:** Graceful handling with error logging

### Statistics and Reporting
- Download statistics: successes, failures, data points collected
- Merge statistics: files processed, countries, timestamps
- Detailed failure lists for troubleshooting

## Advanced Usage

### Large-Scale Downloads
```bash
# Download multiple years with conservative settings
python main.py --start-date 2015-01-01 --end-date 2024-12-31 \
               --delay 2.0 --max-retries 5 \
               --log-level INFO --log-file download.log
```

### Debugging Failed Downloads
```bash
# Run with debug logging
python main.py --start-date 2024-01-01 --end-date 2024-12-31 \
               --log-level DEBUG --log-file debug.log

# Check error responses
ls -lh error_responses_monthly/
cat error_responses_monthly/XX_error_response.txt
```

### Custom Workflows
```bash
# Download only specific regions
echo -e "US\nCA\nMX" > north_america.txt
python main.py --countries-file north_america.txt --start-date 2024-01-01

# Process with full logging
python check_timestamps.py youtube_traffic_data_monthly --log-level DEBUG
python merge_data.py youtube_traffic_data_monthly na_merged.csv --log-level INFO
```

## Troubleshooting

### Common Issues

**Import Error: No module named 'tqdm' or 'requests'**
```bash
pip install -r requirements.txt
```

**API Rate Limiting**
```bash
# Increase delay between requests
python main.py --delay 2.0
```

**Inconsistent Timestamps**
- Run `check_timestamps.py` to identify problematic files
- Re-download failed countries individually
- Check `error_responses_monthly/` directory for clues

**Memory Issues with Large Merges**
- Process countries in batches
- Merge smaller groups first, then combine

### Getting Help
```bash
# Display help for any script
python main.py --help
python check_timestamps.py --help
python merge_data.py --help
```

## Performance Considerations

### Download Times
- ~15,000 API requests for 220 countries × 72 months
- With 0.5s delay: ~2 hours total
- With 1.0s delay: ~4 hours total
- Consider running overnight for full historical data

### Disk Space
- Individual country files: ~50-200 KB each
- Total for 220 countries: ~15-30 MB
- Merged file: ~10 MB for 6 years of data

## Recent Improvements

This project was recently refactored with significant improvements:

✅ **CLI Arguments:** Full configurability without editing code
✅ **Retry Logic:** Automatic retry with exponential backoff
✅ **Proper Logging:** Structured logging with configurable levels
✅ **Type Hints:** Complete type safety for better IDE support
✅ **Shared Utilities:** Eliminated ~150 lines of duplicate code
✅ **Statistics:** Comprehensive tracking and reporting
✅ **Error Handling:** Robust error recovery and reporting
✅ **Production Ready:** Professional code quality and structure

See `REFACTORING.md` for detailed documentation of all improvements.

## Example Workflow

Complete workflow for downloading and analyzing YouTube traffic data:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Download data for 2024
python main.py --start-date 2024-01-01 --end-date 2024-12-31 \
               --log-level INFO --log-file download.log

# 3. Verify timestamp consistency
python check_timestamps.py youtube_traffic_data_monthly

# 4. Merge all country data
python merge_data.py youtube_traffic_data_monthly youtube_2024_merged.csv

# 5. Analyze merged data with your favorite tools
# (pandas, Excel, Tableau, etc.)
```

## Project Structure

```
.
├── main.py                  # Download YouTube traffic data
├── check_timestamps.py      # Verify timestamp consistency
├── merge_data.py            # Merge country files
├── utils.py                 # Shared utilities and constants
├── requirements.txt         # Python dependencies
├── .gitignore              # Git ignore rules
├── README.md               # This file
├── REFACTORING.md          # Detailed refactoring documentation
├── LICENSE                 # MIT License
├── countries codes.txt     # Reference list of country codes
└── example_data/           # Example data and API responses
    ├── raw_api_response_example.txt
    ├── youtube_traffic_merged_data_2024.csv
    └── countries/
        ├── GE.csv
        ├── NL.csv
        └── RU.csv
```

## License

MIT License

## Author

Denis Yagodin

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Changelog

### Version 2.0 (2025)
- Added comprehensive CLI arguments for all scripts
- Implemented retry logic with exponential backoff
- Added proper structured logging with configurable levels
- Created shared utilities module (utils.py)
- Added type hints throughout codebase
- Implemented statistics tracking and reporting
- Enhanced error handling and recovery
- Added dependency management (requirements.txt)
- Improved code organization and maintainability

### Version 1.0 (Initial Release)
- Basic download functionality
- Timestamp consistency checker
- CSV data merger
