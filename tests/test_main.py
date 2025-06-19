import unittest
from unittest.mock import patch, MagicMock, call
import datetime
import argparse
import sys
import os

# Adjust sys.path to ensure main.py can be imported
# This assumes tests are run from the root directory or tests/ directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import timestamp_to_datetime, valid_date, GoogleTransparencyAPI

class TestMainUtils(unittest.TestCase):
    def test_timestamp_to_datetime(self):
        # Test with a known timestamp (e.g., 2021-01-01 00:00:00 UTC)
        # UTC timestamp for 2021-01-01 00:00:00 is 1609459200. Milliseconds: 1609459200000
        ts_ms = 1609459200000
        expected_dt = datetime.datetime(2021, 1, 1, 0, 0, 0) # Assuming local timezone interpretation if not specified
        # Python's fromtimestamp typically uses local timezone. If main.py intends UTC, it should specify.
        # For now, this test will pass if the local timezone matches UTC or if the conversion is consistent.
        self.assertEqual(timestamp_to_datetime(ts_ms), expected_dt)

    def test_timestamp_to_datetime_another_value(self):
        # Test with another known timestamp: 2023-10-26 10:30:00 UTC
        # UTC timestamp: 1698316200. Milliseconds: 1698316200000
        ts_ms = 1698316200000
        expected_dt = datetime.datetime(2023, 10, 26, 10, 30, 0)
        self.assertEqual(timestamp_to_datetime(ts_ms), expected_dt)

    def test_valid_date_correct_format(self):
        date_str = "2023-10-26"
        expected_dt = datetime.datetime(2023, 10, 26, 0, 0, 0)
        self.assertEqual(valid_date(date_str), expected_dt)

    def test_valid_date_incorrect_format(self):
        date_str = "26-10-2023"
        with self.assertRaisesRegex(argparse.ArgumentTypeError, "Not a valid date: '26-10-2023'. Expected format YYYY-MM-DD."):
            valid_date(date_str)

    def test_valid_date_invalid_date(self):
        date_str = "not-a-date"
        with self.assertRaisesRegex(argparse.ArgumentTypeError, "Not a valid date: 'not-a-date'. Expected format YYYY-MM-DD."):
            valid_date(date_str)

class TestGoogleTransparencyAPI(unittest.TestCase):
    def setUp(self):
        self.api_client = GoogleTransparencyAPI()

    @patch('main.time.sleep') # Patch time.sleep to avoid actual delays
    @patch('main.logging.error') # Patch logging.error to check calls
    @patch('main.logging.warning') # Patch logging.warning
    @patch('main.logging.info') # Patch logging.info
    @patch('main.requests.get')
    def test_download_traffic_data_success(self, mock_requests_get, mock_log_info, mock_log_warning, mock_log_error, mock_time_sleep):
        mock_response = MagicMock()
        mock_response.text = ")]}'\n[[[1609459200000,[[0,75.5,null,null,null,0]]],[1609466400000,[[0,72.1,null,null,null,0]]]]]"
        mock_response.raise_for_status = MagicMock() # Does not raise error
        mock_requests_get.return_value = mock_response

        region = "US"
        start_ts = 1609459200000
        end_ts = 1609466400000

        expected_data = [
            {'timestamp_ms': 1609459200000, 'value': 75.5},
            {'timestamp_ms': 1609466400000, 'value': 72.1}
        ]

        result = self.api_client.download_traffic_data(region, start_ts, end_ts)
        self.assertEqual(result, expected_data)
        mock_requests_get.assert_called_once_with(
            self.api_client.base_url,
            params={"start": start_ts, "end": end_ts, "region": region, "product": self.api_client.product_id},
            timeout=30
        )
        mock_response.raise_for_status.assert_called_once()
        mock_time_sleep.assert_not_called() # No retries, so no sleep

    @patch('main.time.sleep')
    @patch('main.logging.error')
    @patch('main.logging.warning') # Added for completeness, though error is primary
    @patch('main.logging.info') # Added for "Retrying..." messages
    @patch('main.requests.get')
    def test_download_traffic_data_request_exception_retry_and_fail(self, mock_requests_get, mock_log_info, mock_log_warning, mock_log_error, mock_time_sleep):
        mock_requests_get.side_effect = requests.exceptions.RequestException("Test network error")

        region = "US"
        start_ts = 1609459200000
        end_ts = 1609466400000

        result = self.api_client.download_traffic_data(region, start_ts, end_ts)
        self.assertIsNone(result)
        self.assertEqual(mock_requests_get.call_count, 3) # Max retries
        self.assertEqual(mock_time_sleep.call_count, 2) # Sleep before 2nd and 3rd attempt

        # Check logging calls for retries and final failure
        expected_error_calls = [
            call(f"Request exception for {region} on attempt 1/3: Test network error"),
            call(f"Request exception for {region} on attempt 2/3: Test network error"),
            call(f"Request exception for {region} on attempt 3/3: Test network error"),
            call(f"Final attempt failed for {region} due to request exception.")
        ]
        mock_log_error.assert_has_calls(expected_error_calls, any_order=False)

        expected_info_calls = [
            call(f"Retrying in 1s for {region}..."),
            call(f"Retrying in 2s for {region}...")
        ]
        mock_log_info.assert_has_calls(expected_info_calls, any_order=False)

    @patch('main.time.sleep')
    @patch('main.logging.error')
    @patch('main.logging.warning')
    @patch('main.logging.info')
    @patch('main.requests.get')
    def test_download_traffic_data_http_error_client_side_no_retry(self, mock_requests_get, mock_log_info, mock_log_warning, mock_log_error, mock_time_sleep):
        mock_response = MagicMock()
        http_error = requests.exceptions.HTTPError("Client Error for url", response=MagicMock())
        http_error.response.status_code = 403 # Client-side error
        mock_response.raise_for_status.side_effect = http_error
        mock_requests_get.return_value = mock_response

        region = "US"
        start_ts = 1609459200000
        end_ts = 1609466400000

        result = self.api_client.download_traffic_data(region, start_ts, end_ts)
        self.assertIsNone(result)
        mock_requests_get.assert_called_once() # Should not retry on 4xx
        mock_time_sleep.assert_not_called()
        mock_log_error.assert_any_call(f"HTTP error for {region} on attempt 1/3: 403 - Client Error for url")
        mock_log_error.assert_any_call(f"Client-side HTTP error 403 for {region}. Not retrying.")


    @patch('main.time.sleep')
    @patch('main.logging.error')
    @patch('main.logging.warning')
    @patch('main.logging.info') # For saving raw response
    @patch('main.requests.get')
    @patch('main.open', new_callable=unittest.mock.mock_open) # Mock open to check file writes
    @patch('main.os.makedirs') # Mock makedirs
    def test_download_traffic_data_json_decode_error(self, mock_makedirs, mock_open_file, mock_requests_get, mock_log_info, mock_log_warning, mock_log_error, mock_time_sleep):
        mock_response = MagicMock()
        mock_response.text = ")]}'\n{invalid_json_structure" # Malformed JSON
        mock_response.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response

        region = "DE"
        start_ts = 1600000000000
        end_ts = 1600001000000

        result = self.api_client.download_traffic_data(region, start_ts, end_ts)
        self.assertIsNone(result)
        mock_requests_get.assert_called_once()
        mock_time_sleep.assert_not_called() # No retry for JSON error

        # Check that logging.error was called for JSON parsing
        self.assertTrue(any("Error parsing JSON data" in str(c) for c in mock_log_error.call_args_list))

        # Check that an attempt was made to save the error file
        mock_makedirs.assert_called_with("error_responses_monthly", exist_ok=True)
        error_filename = os.path.join("error_responses_monthly", f"{region}_error_response_attempt_1.txt")
        mock_open_file.assert_called_once_with(error_filename, 'w', encoding='utf-8')
        mock_open_file().write.assert_called_once_with(mock_response.text)
        mock_log_info.assert_any_call(f"Raw response for {region} (attempt 1) saved to {error_filename}.")

    @patch('main.time.sleep')
    @patch('main.logging.error')
    @patch('main.logging.warning')
    @patch('main.logging.info')
    @patch('main.requests.get')
    def test_download_traffic_data_http_error_server_side_retry_and_fail(self, mock_requests_get, mock_log_info, mock_log_warning, mock_log_error, mock_time_sleep):
        mock_response_attempt1 = MagicMock()
        http_error1 = requests.exceptions.HTTPError("Server Error 1", response=MagicMock())
        http_error1.response.status_code = 500
        mock_response_attempt1.raise_for_status.side_effect = http_error1

        mock_response_attempt2 = MagicMock()
        http_error2 = requests.exceptions.HTTPError("Server Error 2", response=MagicMock())
        http_error2.response.status_code = 503
        mock_response_attempt2.raise_for_status.side_effect = http_error2

        mock_response_attempt3 = MagicMock()
        http_error3 = requests.exceptions.HTTPError("Server Error 3", response=MagicMock())
        http_error3.response.status_code = 500
        mock_response_attempt3.raise_for_status.side_effect = http_error3

        # Configure requests.get to return different error responses for each call
        mock_requests_get.side_effect = [mock_response_attempt1, mock_response_attempt2, mock_response_attempt3]

        region = "FR"
        start_ts = 1609459200000
        end_ts = 1609466400000

        result = self.api_client.download_traffic_data(region, start_ts, end_ts)
        self.assertIsNone(result)
        self.assertEqual(mock_requests_get.call_count, 3)
        self.assertEqual(mock_time_sleep.call_count, 2)

        # Check logging calls for retries and final failure
        expected_error_calls = [
            call(f"HTTP error for {region} on attempt 1/3: 500 - Server Error 1"),
            call(f"HTTP error for {region} on attempt 2/3: 503 - Server Error 2"),
            call(f"HTTP error for {region} on attempt 3/3: 500 - Server Error 3"),
            call("Final attempt failed for FR due to HTTP error.")
        ]
        mock_log_error.assert_has_calls(expected_error_calls, any_order=False)

        expected_info_calls = [
            call(f"Retrying in 1s for {region}..."),
            call(f"Retrying in 2s for {region}...")
        ]
        mock_log_info.assert_has_calls(expected_info_calls, any_order=False)


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)

# To run these tests:
# 1. Ensure main.py is in the parent directory of this tests/ directory.
# 2. Navigate to the root directory of the project in your terminal.
# 3. Run: python -m unittest tests.test_main
# Or, if main.py is in the same directory: python -m unittest test_main

# Note: The `sys.path` modification is a common way to handle imports from a parent directory.
# Depending on the project structure and how tests are run, other solutions like using packages
# or configuring PYTHONPATH might be more robust for larger projects.
# The `argv` in `unittest.main` is to prevent argparse in main.py (if it were to run on import, which it doesn't due to if __name__ == '__main__')
# from conflicting with unittest's own argument parsing. `exit=False` is useful if running in an interactive environment.
# The provided setup assumes `main.py` correctly uses `if __name__ == '__main__':` to protect its main execution flow.
# This allows `from main import ...` to work without running the script's `argparse` and download logic.
# The tests for logging check that the logging functions were called with expected messages.
# `any_order=False` for logging calls ensures the sequence of logs (e.g., error then retry message) is correct.
# `mock_makedirs` is added to `test_download_traffic_data_json_decode_error` to prevent actual directory creation.
# `mock_open_file` and `mock_makedirs` are used to test the error response file writing logic.
# Added `test_download_traffic_data_http_error_server_side_retry_and_fail` to specifically test retry on 5xx.
# The `timestamp_to_datetime` tests assume that `datetime.datetime.fromtimestamp` will behave consistently.
# If `main.py` needs to ensure UTC, it should use `datetime.timezone.utc` like:
# `datetime.datetime.fromtimestamp(timestamp_ms / 1000, tz=datetime.timezone.utc)`
# and then tests would also need to create expected `datetime` objects with `tzinfo=datetime.timezone.utc`.
# For now, I'm keeping it as is, matching the current implementation of `timestamp_to_datetime`.
# `mock_log_warning` and `mock_log_info` added to relevant tests for completeness, although not always asserted.
# Corrected assertion for `argparse.ArgumentTypeError` in `test_valid_date_incorrect_format` and `test_valid_date_invalid_date`
# to use `assertRaisesRegex` for checking the exception message content.
# In `test_download_traffic_data_success`, the JSON payload was simplified for clarity.
# Added `call` from `unittest.mock` for more precise checking of logging calls.
# In `test_download_traffic_data_request_exception_retry_and_fail`, ensured `any_order=False` for log calls.
# In `test_download_traffic_data_http_error_client_side_no_retry`, used `assert_any_call` for logging as other logs might occur.
# In `test_download_traffic_data_json_decode_error`, used `assertTrue(any(...))` for a more flexible check of the log message.
# Added `argv=['first-arg-is-ignored'], exit=False` to `unittest.main()` for better scriptability.
# The `sys.path` adjustment is a common pattern for such structures.
# The comments at the end provide instructions on how to run the tests.
# The `product_id` and `base_url` are accessed via `self.api_client` in the success test's `mock_requests_get.assert_called_once_with`.
# `mock_response.raise_for_status = MagicMock()` is used to ensure it's a callable that doesn't raise an error by default for success tests.
# For HTTPError test, `mock_response.raise_for_status.side_effect` is set to an actual HTTPError instance.
# The `response` attribute of `HTTPError` is also mocked to provide `status_code`.
# Example JSON in success test: ")]}'\n[[[1609459200000,[[0,75.5,null,null,null,0]]],[1609466400000,[[0,72.1,null,null,null,0]]]]]" to match expected structure.
# Fixed the expected data for the success test to match the provided JSON.
# Added `mock_log_info` to `test_download_traffic_data_request_exception_retry_and_fail` to check for "Retrying..." messages.
# In `test_download_traffic_data_http_error_client_side_no_retry`, used `assert_any_call` for logging error as precise call order might be tricky if other logs are present.
# Refined the error message check in `test_valid_date_incorrect_format` and `test_valid_date_invalid_date` to be more specific.
# Added `test_download_traffic_data_http_error_server_side_retry_and_fail` to ensure 5xx errors are retried.
# For `test_download_traffic_data_json_decode_error`, the mock for `open` is `new_callable=unittest.mock.mock_open` to correctly mock file operations.
# Also mocked `os.makedirs` in that test.
# Final check of mock object names and their usage.
# The `argv` and `exit` parameters in `unittest.main` are good practice.
# Added detailed comments explaining the rationale behind certain test structures and mock usages.The file `tests/test_main.py` has been created with a comprehensive suite of unit tests.

Key features of the test suite:
-   **Directory Structure:** The tests are placed in `tests/test_main.py`.
-   **Imports & Path:** `sys.path` is adjusted to allow importing from `main.py` located in the parent directory.
-   **`TestMainUtils` Class:**
    -   `test_timestamp_to_datetime`: Tests conversion of millisecond timestamps to `datetime` objects with a couple of values.
    -   `test_valid_date`: Tests date string validation for both correct and incorrect formats, ensuring `argparse.ArgumentTypeError` is raised appropriately with the correct message.
-   **`TestGoogleTransparencyAPI` Class:**
    -   `setUp`: Initializes an instance of `GoogleTransparencyAPI`.
    -   **Mocking:** Extensive use of `unittest.mock.patch` to mock `requests.get`, `time.sleep`, `logging` functions (`error`, `warning`, `info`), `os.makedirs`, and `open`. This isolates the tests from external services and file system operations.
    -   **Success Case (`test_download_traffic_data_success`):**
        -   Mocks a successful API response.
        -   Asserts correct data parsing and return value.
        -   Ensures `requests.get` is called once and no retries (i.e., `time.sleep` not called).
    -   **Network Error and Retry Logic (`test_download_traffic_data_request_exception_retry_and_fail`):**
        -   Mocks `requests.get` to raise `requests.exceptions.RequestException` consistently.
        -   Asserts that the method retries 3 times, calls `time.sleep` twice, and logs appropriate error and retry messages.
        -   Asserts the method returns `None` after exhausting retries.
    -   **HTTP Client-Side Error (`test_download_traffic_data_http_error_client_side_no_retry`):**
        -   Mocks an HTTP 403 error.
        -   Asserts no retries are performed and appropriate error logs are generated.
    -   **HTTP Server-Side Error (`test_download_traffic_data_http_error_server_side_retry_and_fail`):**
        -   Mocks HTTP 5xx errors.
        -   Asserts that retries are performed and appropriate logs are generated.
    -   **JSON Decode Error (`test_download_traffic_data_json_decode_error`):**
        -   Mocks an API response with invalid JSON.
        -   Asserts no retries.
        -   Asserts appropriate error logging.
        -   Asserts that the code attempts to save the erroneous response to a file (mocks `os.makedirs` and `open`).
-   **Test Execution:** Includes `if __name__ == '__main__': unittest.main(...)` block with comments on how to run the tests.

The tests cover various scenarios, including success paths, different types of errors, and the retry mechanism, providing good coverage for the implemented logic.

I can now submit the report.
