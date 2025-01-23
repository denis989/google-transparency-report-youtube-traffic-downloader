import requests
import datetime
import csv
import json
import time
import os
from tqdm.notebook import tqdm  # Progress bar for notebooks (and general use if tqdm is installed)

def timestamp_to_datetime(timestamp_ms):
    """
    Converts a timestamp in milliseconds to a datetime object.

    Args:
        timestamp_ms (int): Timestamp in milliseconds.

    Returns:
        datetime.datetime: Datetime object corresponding to the timestamp.
    """
    return datetime.datetime.fromtimestamp(timestamp_ms / 1000)

def download_traffic_data(region_code, start_timestamp_ms, end_timestamp_ms):
    """
    Downloads YouTube traffic data from Google Transparency Report API for a given region and time range.

    Args:
        region_code (str): ISO 3166-1 alpha-2 region code (e.g., "US", "RU").
        start_timestamp_ms (int): Start timestamp of the data range in milliseconds.
        end_timestamp_ms (int): End timestamp of the data range in milliseconds.

    Returns:
        list or None: A list of data points (dictionaries with timestamp_ms and value) if download is successful,
                     None if download fails or data parsing encounters an error.
    """
    base_url = "https://transparencyreport.google.com/transparencyreport/api/v3/traffic/fraction"
    params = {
        "start": start_timestamp_ms,
        "end": end_timestamp_ms,
        "region": region_code,
        "product": 21  # Product ID for YouTube traffic
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        content = response.text

        if content.startswith(")]}'\n"): # Remove security prefix
            content = content[5:]

        if not content.strip(): # Check for empty response
            print(f"Warning: Empty response received for {region_code}.")
            return None

        try:
            data = json.loads(content) # Parse JSON response
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON data for {region_code}: {e}")
            print(f"Raw response content for {region_code}:\n{content}")
            error_dir = "error_responses_monthly" # Directory to save error responses
            os.makedirs(error_dir, exist_ok=True)
            error_filename = os.path.join(error_dir, f"{region_code}_error_response.txt")
            with open(error_filename, 'w', encoding='utf-8') as error_file:
                error_file.write(content) # Save raw response to file
            print(f"Raw response saved to {error_filename} for debugging.")
            return None

        data_points = []
        # Data structure validation before processing
        if isinstance(data, list) and data and isinstance(data[0], list) and len(data[0]) > 1 and isinstance(data[0][1], list):
            for point in data[0][1]:
                if isinstance(point, list) and len(point) >= 2 and isinstance(point[1], list) and point[1] and isinstance(point[1][0], list) and len(point[1][0]) >= 2:
                    timestamp_ms = point[0]
                    value = point[1][0][1] if point[1][0][1] is not None else None # Extract value, handle nulls
                    if value is not None:
                        data_points.append({'timestamp_ms': timestamp_ms, 'value': value})
        return data_points

    except requests.exceptions.RequestException as e: # Handle download errors
        print(f"Error downloading data for {region_code}: {e}")
        return None
    except IndexError as e: # Handle index errors in data structure
        print(f"Error processing data structure for {region_code}: {e}")
        return None

def save_to_csv(region_code, data_points, output_dir="."):
    """
    Saves traffic data to a CSV file in the specified output directory.

    Args:
        region_code (str): ISO 3166-1 alpha-2 region code.
        data_points (list): List of data points to save.
        output_dir (str): Directory where the CSV file will be saved. Defaults to the current directory.
    """
    if not data_points: # Check if there is data to save
        print(f"No data to save for {region_code}.")
        return

    filename = os.path.join(output_dir, f"{region_code}.csv") # Create filepath
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile: # Open file for writing CSV
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(['date and time', 'value']) # Write header row
            for point in data_points:
                datetime_obj = timestamp_to_datetime(point['timestamp_ms'])
                datetime_str = datetime_obj.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] # Format datetime to string with milliseconds
                csv_writer.writerow([datetime_str, point['value']]) # Write data row
        print(f"Data for {region_code} saved to {filename}")
    except Exception as e: # Handle file writing errors
        print(f"Error saving CSV file for {region_code}: {e}")

if __name__ == '__main__':
    country_codes = [["OM"],["MV"],["BJ"],["NZ"],["MD"],["AW"],["CN"],["EE"],["HR"],["AE"],["SL"],["FI"],["BI"],["VG"],["GM"],["ID"],["YT"],["TR"],["VI"],["AX"],["CO"],["MW"],["LA"],["FJ"],["ME"],["KN"],["PR"],["GN"],["IE"],["LR"],["NI"],["AF"],["AU"],["US"],["CL"],["EC"],["ZW"],["UA"],["BY"],["IT"],["ET"],["VE"],["NF"],["MS"],["QA"],["BG"],["TN"],["RW"],["MU"],["MC"],["CM"],["NG"],["AD"],["SK"],["BZ"],["MT"],["BH"],["TO"],["GL"],["VU"],["KI"],["IR"],["PM"],["BW"],["SH"],["MQ"],["KZ"],["TL"],["BE"],["RU"],["GI"],["VC"],["PL"],["AR"],["SY"],["CI"],["MA"],["AT"],["CK"],["RE"],["NE"],["SI"],["DO"],["IS"],["BF"],["ES"],["TM"],["SZ"],["HN"],["JE"],["MR"],["LK"],["GY"],["TJ"],["RS"],["CY"],["GG"],["CG"],["HK"],["MO"],["DK"],["SG"],["DM"],["IQ"],["KH"],["CZ"],["GH"],["NC"],["KY"],["MP"],["BD"],["KG"],["ZA"],["PK"],["CH"],["TH"],["BA"],["GE"],["LI"],["FR"],["MM"],["IM"],["PH"],["SC"],["BR"],["GF"],["NA"],["SE"],["BT"],["KW"],["MN"],["BB"],["NR"],["AO"],["CF"],["SV"],["TZ"],["BS"],["SD"],["DJ"],["KE"],["IN"],["MK"],["CU"],["RO"],["PF"],["NO"],["AL"],["SA"],["VN"],["TW"],["GT"],["PW"],["GB"],["JO"],["ML"],["PY"],["CV"],["TG"],["GD"],["AM"],["PG"],["CD"],["ST"],["DZ"],["SB"],["GU"],["IL"],["NP"],["LY"],["WS"],["JP"],["CA"],["BN"],["DE"],["GR"],["LV"],["UY"],["CR"],["TC"],["JM"],["MZ"],["MH"],["SR"],["FO"],["ZM"],["PE"],["BO"],["TV"],["KR"],["TD"],["UZ"],["GA"],["GP"],["LT"],["YE"],["HT"],["LB"],["MX"],["PS"],["EG"],["LS"],["PA"],["AG"],["SN"],["NL"],["LU"],["AI"],["UG"],["MY"],["LC"],["BM"],["TT"],["GQ"],["PT"],["AZ"],["HU"],["SO"],["MG"]] # List of country codes to download data for
    start_date_period = datetime.datetime(2019, 1, 1, 0, 0, 0) # Start date for data download period
    end_date_period = datetime.datetime(2025, 1, 20, 23, 59, 59) # End date for data download period

    output_directory = "youtube_traffic_data_monthly" # Output directory for CSV files (relative to script location)
    error_directory = "error_responses_monthly" # Output directory for error responses (relative to script location)
    os.makedirs(output_directory, exist_ok=True) # Create output directory if it doesn't exist
    os.makedirs(error_directory, exist_ok=True) # Create error directory if it doesn't exist

    total_months = 0
    current_date_calc = start_date_period
    while current_date_calc < end_date_period: # Calculate total months to process for progress bar
        total_months += 1
        current_date_calc = current_date_calc.replace(day=28) + datetime.timedelta(days=4)
        current_date_calc = current_date_calc.replace(day=1) - datetime.timedelta(days=1) + datetime.timedelta(days=1)

    progress_bar = tqdm(total=len(country_codes) * total_months, desc="Total Progress") # Initialize progress bar

    start_time = time.time() # Record start time for ETA calculation

    for country_info in country_codes: # Loop through each country code
        country_code = country_info[0]
        all_data_points = [] # List to store all data points for the current country
        current_date = start_date_period # Reset current date to start of period for each country

        while current_date < end_date_period: # Loop through months within the period
            month_start_date = current_date
            month_end_date = current_date.replace(day=28) + datetime.timedelta(days=4) # Rough end of month
            month_end_date = month_end_date.replace(day=1) - datetime.timedelta(days=1) # Exact end of month
            if month_end_date > end_date_period: # Cap month end date to overall period end
                month_end_date = end_date_period

            start_timestamp_ms = int(month_start_date.timestamp() * 1000) # Convert datetime to timestamp (ms)
            end_timestamp_ms = int(month_end_date.timestamp() * 1000) # Convert datetime to timestamp (ms)

            status_message = f"Downloading data for {country_code} month: {month_start_date.strftime('%Y-%m')}"
            print(f"\r{status_message}", end="") # Print status message on single line

            monthly_data_points = download_traffic_data(country_code, start_timestamp_ms, end_timestamp_ms) # Download data for the month

            if monthly_data_points:
                all_data_points.extend(monthly_data_points) # Extend list with monthly data points

            progress_bar.update(1) # Update progress bar after each month

            months_processed = progress_bar.n / len(country_codes) if len(country_codes) > 0 else 0 # Calculate months processed for ETA
            elapsed_time = time.time() - start_time # Calculate elapsed time
            estimated_time_per_month = elapsed_time / max(1, progress_bar.n) if progress_bar.n > 0 else 0 # Estimate time per month
            remaining_months = total_months - months_processed # Calculate remaining months
            estimated_remaining_time_sec = remaining_months * estimated_time_per_month # Estimate remaining time in seconds
            estimated_remaining_time_str = str(datetime.timedelta(seconds=int(estimated_remaining_time_sec))) # Format remaining time to string

            progress_percent = (progress_bar.n / progress_bar.total) * 100 # Calculate overall progress percentage
            progress_bar.set_description(f"Total Progress: {progress_percent:.2f}% - ETA: {estimated_remaining_time_str}") # Update progress bar description with ETA


            current_date = month_end_date + datetime.timedelta(days=1) # Move to the next month
            time.sleep(0.5) # Delay to be nice to the API

        print(f"\rDownloading data for {country_code} complete.        ") # Final status message for country
        if all_data_points:
            save_to_csv(country_code, all_data_points, output_directory) # Save data to CSV file
        else:
            print(f"No data downloaded for {country_code} for the entire period.")

    progress_bar.close() # Close progress bar
    print("Download and save process complete.") # Final completion message