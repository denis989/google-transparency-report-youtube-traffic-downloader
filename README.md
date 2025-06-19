# Google Transparency Report YouTube Traffic Downloader and Merger

## Project Overview

This project provides Python scripts to automatically download YouTube traffic data from the Google Transparency Report API and merge it into a single CSV file for analysis. The scripts are designed to:

1.  **Download YouTube Traffic Data:**  Fetch traffic fraction data for multiple countries over a specified time period from the Google Transparency Report API.
2.  **Ensure Data Consistency:** Check if downloaded CSV files have consistent timestamps, which is crucial for merging data correctly.
3.  **Merge Data into a Single File:** Combine data from individual country CSV files into one consolidated CSV file, making it easier to analyze and compare traffic trends across different regions.

This project is useful for researchers, analysts, or anyone interested in studying global YouTube traffic patterns as reported by Google's Transparency Report.

## Algorithm and Data Flow

The project consists of the following main steps:

1.  **Data Download (using `main.py`):**
    *   The `main.py` script iterates through a list of country codes.
    *   For each country, it breaks down the specified date range (e.g., 2019-01-01 to 2025-01-20) into month-long intervals.
    *   For each month, it sends a request to the Google Transparency Report API to download traffic fraction data for the country and month.
    *   The API response, containing timestamped traffic data points, is parsed from JSON format.
    *   The data points for each month are appended to a list for the respective country.
    *   After downloading data for all months in the specified period for a country, the script saves all collected data points into a separate CSV file named `{country_code}.csv` in the `youtube_traffic_data_monthly` directory.

2.  **Timestamp Consistency Check (using `check_timestamps.py`):**
    *   The `check_timestamps.py` script takes the directory containing the downloaded CSV files as input.
    *   It reads each CSV file and extracts all unique timestamps from the 'date and time' column.
    *   It compares the timestamps from each file against the timestamps from the first file processed (considered as the reference).
    *   The script reports if timestamps are consistent across all files, or if there are any missing, extra, or different timestamps in any file. This step is crucial to ensure data integrity before merging.

3.  **Data Merging (using `merge_data.py`):**
    *   The `merge_data.py` script also takes the directory with country CSV files as input, as well as a path for the output merged CSV file.
    *   It reads each country CSV file and extracts the 'date and time' and 'value' columns.
    *   It merges the data from all country files into a single dictionary, using the 'date and time' as the key and country codes as sub-keys to store the corresponding 'value'.
    *   Finally, it writes the merged data into a single CSV file, with 'date and time' as the first column and each country code as a separate column for traffic values. Missing values are filled with 'NA'.

## Data Granularity

During the investigation, we found that the Google Transparency Report API provides data with **adaptive granularity**, which depends on the time range you request:

*   **Short Time Ranges (e.g., 1 day, 1 week):** The API provides data with **30-minute granularity**. This means you get a data point every 30 minutes.
*   **Longer Time Ranges (e.g., 1 month):** The API automatically aggregates data to a coarser granularity of **2 hours**.
*   **Granularity is API-Driven:** You cannot explicitly control the granularity through API parameters. The API dynamically adjusts the granularity based on the requested time span.

**Granularity Used in these Scripts:**

*   The `main.py` script is designed to download data in **month-long windows**. Therefore, the downloaded data will have a **2-hour granularity**.
*   If you need data with a higher 30-minute granularity, you would need to modify the `main.py` script to download data in smaller time intervals (e.g., day by day or week by week). However, for the current script configuration (monthly downloads), the data will be at a 2-hour granularity.

## Script Descriptions

### `main.py` - YouTube Traffic Data Downloader

*   **Purpose:** Downloads YouTube traffic data from the Google Transparency Report API for a list of countries over a specified period.
*   **Functionality:**
    *   Iterates through a predefined list of country codes.
    *   For each country, downloads data month by month for the period from January 1, 2019, to January 20, 2025.
    *   Saves each country's monthly data into separate CSV files in the `youtube_traffic_data_monthly` directory within the project's root directory.
    *   Includes error handling, progress bar, and ETA estimation.
*   **How to Run:**
    The script now requires command-line arguments to specify country codes, start date, and end date.
    ```bash
    python main.py --country_codes "US,CA,MX" --start_date "YYYY-MM-DD" --end_date "YYYY-MM-DD"
    ```
    *   `--country_codes`: A comma-separated string of ISO 3166-1 alpha-2 country codes (e.g., "US,CA,GB").
    *   `--start_date`: The start date for the data download period in YYYY-MM-DD format.
    *   `--end_date`: The end date for the data download period in YYYY-MM-DD format.
    *   Make sure you have the required Python libraries installed (see "Installation" section).
    *   The script will create `youtube_traffic_data_monthly` and `error_responses_monthly` directories in the same directory where you run the script.

    **Example:**
    ```bash
    python main.py --country_codes "FR,DE,IT" --start_date "2022-01-01" --end_date "2022-12-31"
    ```
    This command will download data for France, Germany, and Italy from January 1, 2022, to December 31, 2022.

### `check_timestamps.py` - CSV Timestamp Consistency Checker

*   **Purpose:** Verifies if all CSV files in a given directory have consistent timestamps in the 'date and time' column.
*   **Functionality:**
    *   Reads CSV files from a specified input directory.
    *   Extracts and compares timestamps from each file to ensure they are identical across all files.
    *   Reports any inconsistencies, such as missing or extra timestamps, or different timestamps at the same positions.
*   **How to Run:**
    ```bash
    python check_timestamps.py <path_to_youtube_traffic_data_monthly_directory>
    ```
    *   Replace `<path_to_youtube_traffic_data_monthly_directory>` with the path to the directory containing your downloaded country CSV files.
    *   Example: `python check_timestamps.py youtube_traffic_data_monthly`

### `merge_data.py` - CSV Data Merger

*   **Purpose:** Merges multiple country-specific CSV files into a single consolidated CSV file.
*   **Functionality:**
    *   Reads CSV files from a specified input directory (e.g., the output directory from `main.py`).
    *   Combines data from all CSV files based on the 'date and time' column.
    *   Creates a new CSV file with columns: 'date and time' and columns for each country code, containing the corresponding traffic values.
    *   Handles missing values by filling them with 'NA' in the merged file.
*   **How to Run:**
    ```bash
    python merge_data.py <path_to_youtube_traffic_data_monthly_directory> <path_to_output_merged_csv_file>
    ```
    *   Replace `<path_to_youtube_traffic_data_monthly_directory>` with the path to the directory containing your country CSV files.
    *   Replace `<path_to_output_merged_csv_file>` with the desired path and filename for the output merged CSV file (e.g., `youtube_traffic_merged_data.csv`).
    *   Example: `python merge_data.py youtube_traffic_data_monthly youtube_traffic_merged_data.csv`

## Installation

1.  **Python:** Ensure you have Python 3.x installed on your system.
2.  **Python Libraries:** Install the required Python libraries using pip:
    ```bash
    pip install requests tqdm
    ```
    *   `requests`: For making HTTP requests to the Google API.
    *   `tqdm`: For displaying progress bars (optional, but recommended).

## Usage

1.  **Download Data:** Run `main.py` with the required command-line arguments to download YouTube traffic data.
    ```bash
    python main.py --country_codes "US,CA" --start_date "2023-01-01" --end_date "2023-03-31"
    ```
    Remember to replace the example values with your desired country codes and date range.
2.  **Check Timestamps:** Run `check_timestamps.py` to verify the consistency of timestamps across the downloaded CSV files.
3.  **Merge Data:** Run `merge_data.py` to merge all country CSV files into a single CSV file for combined analysis.

## Output Files

*   **`youtube_traffic_data_monthly/`**:  Directory where country-specific CSV files are saved after running `main.py`. Each file is named `{country_code}.csv`.
*   **`youtube_traffic_merged_data.csv`**:  The merged CSV file created by `merge_data.py`, containing data for all countries in a single file.
*   **`error_responses_monthly/`**: Directory where raw API responses are saved if errors occur during data download in `main.py`.

## License

MIT License

## Author

Denis Yagodin

