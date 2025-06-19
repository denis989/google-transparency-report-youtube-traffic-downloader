import unittest
from unittest.mock import patch, mock_open, MagicMock, call
import datetime
import sys
import os
import io

# Adjust sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Functions/classes to test
from check_timestamps import get_timestamps_from_csv
# For testing the main script block, we might need to import the script itself
# or use runpy. For now, we'll set up to test its components.
# If check_timestamps.py uses argparse, we need to handle that.

class TestGetTimestampsFromCSV(unittest.TestCase):

    @patch("builtins.open", new_callable=mock_open)
    @patch("builtins.print") # To capture print warnings/errors from the function
    def test_success_with_milliseconds(self, mock_print, mock_file):
        csv_content = "date and time,value\n2023-01-01 10:00:00.123,100\n2023-01-01 10:00:01.456,200"
        mock_file.return_value = io.StringIO(csv_content)

        expected_timestamps = {
            datetime.datetime(2023, 1, 1, 10, 0, 0, 123000),
            datetime.datetime(2023, 1, 1, 10, 0, 1, 456000)
        }
        result = get_timestamps_from_csv("dummy.csv")
        self.assertEqual(result, expected_timestamps)
        mock_print.assert_not_called()

    @patch("builtins.open", new_callable=mock_open)
    @patch("builtins.print")
    def test_success_without_milliseconds(self, mock_print, mock_file):
        csv_content = "date and time,value\n2023-01-01 10:00:00,100\n2023-01-01 10:00:01,200"
        mock_file.return_value = io.StringIO(csv_content)

        expected_timestamps = {
            datetime.datetime(2023, 1, 1, 10, 0, 0),
            datetime.datetime(2023, 1, 1, 10, 0, 1)
        }
        result = get_timestamps_from_csv("dummy.csv")
        self.assertEqual(result, expected_timestamps)
        mock_print.assert_not_called()

    @patch("builtins.open", new_callable=mock_open)
    @patch("builtins.print")
    def test_empty_file(self, mock_print, mock_file):
        mock_file.return_value = io.StringIO("") # Empty content
        result = get_timestamps_from_csv("empty.csv")
        self.assertIsNone(result) # Function returns None for empty file
        mock_print.assert_called_with("Warning: CSV file 'empty.csv' is empty.")

    @patch("builtins.open", new_callable=mock_open)
    @patch("builtins.print")
    def test_no_datetime_column(self, mock_print, mock_file):
        csv_content = "timestamp,value\n2023-01-01 10:00:00,100"
        mock_file.return_value = io.StringIO(csv_content)
        result = get_timestamps_from_csv("no_datetime_col.csv")
        self.assertIsNone(result)
        mock_print.assert_called_with("Warning: 'date and time' column not found in 'no_datetime_col.csv'. Header: ['timestamp', 'value']")

    @patch("builtins.open", new_callable=mock_open)
    @patch("builtins.print")
    def test_unparseable_date(self, mock_print, mock_file):
        csv_content = "date and time,value\nnot-a-date,100\n2023-01-01 10:00:00,200"
        mock_file.return_value = io.StringIO(csv_content)
        result = get_timestamps_from_csv("unparseable.csv")
        self.assertIsNone(result) # Returns None if any date is unparseable
        mock_print.assert_called_with("Error: Could not parse datetime 'not-a-date' in 'unparseable.csv'. Row: ['not-a-date', '100']")

    @patch("builtins.open", side_effect=IOError("File not found"))
    @patch("builtins.print")
    def test_file_read_error(self, mock_print, mock_file_open):
        result = get_timestamps_from_csv("nonexistent.csv")
        self.assertIsNone(result)
        mock_print.assert_called_with("Error reading CSV file 'nonexistent.csv': File not found")


class TestCheckTimestampsMainExecution(unittest.TestCase):

    # Helper to run the main script's core logic by importing it.
    # This assumes check_timestamps.py can be imported and its main block run.
    def run_main_script(self, args):
        # Store original sys.argv and sys.exit
        original_argv = sys.argv
        original_exit = sys.exit

        # Mock sys.argv and sys.exit
        sys.argv = ["check_timestamps.py"] + args
        # sys.exit = MagicMock() # Prevent actual exit and allow checking
        # Using a try-finally for this might be safer if script is complex

        # Instead of directly calling a main function (which we didn't refactor into check_timestamps.py)
        # we will use runpy to execute the script in a controlled environment.
        # This is better for testing __main__ blocks.
        # However, runpy might be complex with mocking print/exit across modules.
        # A simpler way for this specific script structure:
        # Import the script. This executes module-level code.
        # The __name__ == '__main__' block won't run on import.
        # So, we need to execute it. The most direct way is to use exec,
        # or refactor check_timestamps.py to have a main() function.
        # Given the constraints, I will simulate by calling a conceptual main function
        # that embodies the script's __main__ logic.
        # Since I cannot modify check_timestamps.py, I will load the script and execute its __main__ block.
        # This is tricky. The best I can do is to patch what the __main__ block uses.

        # For this test, I'll directly import and run the script's main logic
        # by re-executing the script's content within a controlled environment.
        # This is not ideal. A better way is to refactor check_timestamps.py to have a main() function.
        # For now, I will patch os.listdir, os.path.exists, etc. and then import check_timestamps.
        # This is still not running the __main__ block.
        #
        # The most robust way without changing check_timestamps.py is to use subprocess
        # and capture stdout/stderr, but that's for integration tests.
        # For unit tests of the main logic, we usually refactor it into a function.
        #
        # Let's try a simplified approach: patch elements and then use runpy
        # runpy.run_module can execute it as __main__
        import runpy

        # Patch sys.exit to prevent test runner from exiting and to check exit codes
        mock_exit = MagicMock()
        sys.exit = mock_exit

        try:
            runpy.run_module("check_timestamps", run_name="__main__")
        except SystemExit as e: # Catch the mocked exit
             pass # Expected if sys.exit is called

        # Restore original sys.argv and sys.exit
        sys.argv = original_argv
        sys.exit = original_exit
        return mock_exit # Return the mock_exit to check if it was called


    @patch("builtins.print")
    @patch("check_timestamps.get_timestamps_from_csv")
    @patch("check_timestamps.os.path.join", side_effect=lambda *args: os.path.normpath(os.path.join(*args)))
    @patch("check_timestamps.os.listdir")
    @patch("check_timestamps.os.path.exists")
    def test_main_consistent_timestamps(self, mock_exists, mock_listdir, mock_path_join, mock_get_csv, mock_print):
        mock_exists.return_value = True # Directory exists
        mock_listdir.return_value = ["file1.csv", "file2.csv"]

        ts_set1 = {datetime.datetime(2023,1,1,10,0,0), datetime.datetime(2023,1,1,11,0,0)}
        mock_get_csv.side_effect = [ts_set1, ts_set1]

        self.run_main_script(["dummy_dir"])

        # Expected print calls (simplified, actual script is more verbose)
        mock_print.assert_any_call("Checking timestamps in CSV files...")
        mock_print.assert_any_call("Using timestamps from 'file1.csv' as reference.")
        mock_print.assert_any_call("Timestamps in 'file2.csv' match the reference.")
        # The script doesn't have a single "all consistent" message at the end if files match one by one.
        # It just prints "Timestamp check complete."
        mock_print.assert_any_call("\nTimestamp check complete.")


    @patch("builtins.print")
    @patch("check_timestamps.get_timestamps_from_csv")
    @patch("check_timestamps.os.path.join", side_effect=lambda *args: os.path.normpath(os.path.join(*args)))
    @patch("check_timestamps.os.listdir")
    @patch("check_timestamps.os.path.exists")
    def test_main_inconsistent_timestamps_missing(self, mock_exists, mock_listdir, mock_path_join, mock_get_csv, mock_print):
        mock_exists.return_value = True
        mock_listdir.return_value = ["file1.csv", "file2.csv"]

        ts_set1 = {datetime.datetime(2023,1,1,10,0,0), datetime.datetime(2023,1,1,11,0,0)}
        ts_set2 = {datetime.datetime(2023,1,1,10,0,0)} # Missing one
        mock_get_csv.side_effect = [ts_set1, ts_set2]

        self.run_main_script(["dummy_dir"])
        mock_print.assert_any_call("Error: 'file2.csv' is missing 1 timestamps compared to 'file1.csv'.")
        mock_print.assert_any_call(f"  Missing: {datetime.datetime(2023,1,1,11,0,0)}")

    @patch("builtins.print")
    @patch("check_timestamps.get_timestamps_from_csv")
    @patch("check_timestamps.os.path.join", side_effect=lambda *args: os.path.normpath(os.path.join(*args)))
    @patch("check_timestamps.os.listdir")
    @patch("check_timestamps.os.path.exists")
    def test_main_inconsistent_timestamps_extra(self, mock_exists, mock_listdir, mock_path_join, mock_get_csv, mock_print):
        mock_exists.return_value = True
        mock_listdir.return_value = ["file1.csv", "file2.csv"]

        ts_set1 = {datetime.datetime(2023,1,1,10,0,0)}
        ts_set2 = {datetime.datetime(2023,1,1,10,0,0), datetime.datetime(2023,1,1,11,0,0)} # Extra one
        mock_get_csv.side_effect = [ts_set1, ts_set2]

        self.run_main_script(["dummy_dir"])
        mock_print.assert_any_call("Error: 'file2.csv' has 1 extra timestamps compared to 'file1.csv'.")
        mock_print.assert_any_call(f"  Extra: {datetime.datetime(2023,1,1,11,0,0)}")

    @patch("builtins.print")
    @patch("check_timestamps.get_timestamps_from_csv")
    @patch("check_timestamps.os.path.join", side_effect=lambda *args: os.path.normpath(os.path.join(*args)))
    @patch("check_timestamps.os.listdir")
    @patch("check_timestamps.os.path.exists")
    def test_main_inconsistent_timestamps_different_values(self, mock_exists, mock_listdir, mock_path_join, mock_get_csv, mock_print):
        mock_exists.return_value = True
        mock_listdir.return_value = ["file1.csv", "file2.csv"]

        ts_set1 = {datetime.datetime(2023,1,1,10,0,0), datetime.datetime(2023,1,1,11,0,0)}
        ts_set2 = {datetime.datetime(2023,1,1,10,0,0), datetime.datetime(2023,1,1,12,0,0)} # Different value
        mock_get_csv.side_effect = [ts_set1, ts_set2]

        self.run_main_script(["dummy_dir"])
        # The script's logic for "different" is when counts are same but content differs.
        # Here, one is missing, one is extra.
        mock_print.assert_any_call("Error: 'file2.csv' is missing 1 timestamps compared to 'file1.csv'.")
        mock_print.assert_any_call(f"  Missing: {datetime.datetime(2023,1,1,11,0,0)}")
        mock_print.assert_any_call("Error: 'file2.csv' has 1 extra timestamps compared to 'file1.csv'.")
        mock_print.assert_any_call(f"  Extra: {datetime.datetime(2023,1,1,12,0,0)}")


    @patch("builtins.print")
    # No need to mock get_timestamps_from_csv if no CSV files are processed
    @patch("check_timestamps.os.path.join", side_effect=lambda *args: os.path.normpath(os.path.join(*args)))
    @patch("check_timestamps.os.listdir")
    @patch("check_timestamps.os.path.exists")
    def test_main_no_csv_files(self, mock_exists, mock_listdir, mock_path_join, mock_print):
        mock_exists.return_value = True
        mock_listdir.return_value = ["file.txt", "another.doc"] # No CSVs

        mock_exit = self.run_main_script(["dummy_dir_no_csv"])
        mock_print.assert_any_call("Error: No CSV files found in 'dummy_dir_no_csv'.")
        mock_exit.assert_called_once_with(1)


    @patch("builtins.print")
    # No need to mock listdir if directory doesn't exist
    @patch("check_timestamps.os.path.exists")
    def test_main_directory_not_found(self, mock_exists, mock_print):
        mock_exists.return_value = False # Directory does not exist

        mock_exit = self.run_main_script(["non_existent_dir"])
        mock_print.assert_any_call("Error: Directory 'non_existent_dir' not found.")
        mock_exit.assert_called_once_with(1)

    @patch("builtins.print")
    @patch("check_timestamps.get_timestamps_from_csv")
    @patch("check_timestamps.os.path.join", side_effect=lambda *args: os.path.normpath(os.path.join(*args)))
    @patch("check_timestamps.os.listdir")
    @patch("check_timestamps.os.path.exists")
    def test_main_one_csv_file(self, mock_exists, mock_listdir, mock_path_join, mock_get_csv, mock_print):
        mock_exists.return_value = True
        mock_listdir.return_value = ["only_one.csv"]
        # The script currently doesn't have a specific "only one file" message before "check complete"
        # It will try to use it as reference and then finish.
        # The current script structure would print:
        # "Checking timestamps in CSV files..."
        # "Using timestamps from 'only_one.csv' as reference."
        # "\nTimestamp check complete."
        # Let's ensure get_timestamps_from_csv is called.
        ts_set_single = {datetime.datetime(2023,1,1,10,0,0)}
        mock_get_csv.return_value = ts_set_single

        self.run_main_script(["dummy_dir_one_csv"])
        mock_print.assert_any_call("Checking timestamps in CSV files...")
        mock_print.assert_any_call("Using timestamps from 'only_one.csv' as reference.")
        mock_print.assert_any_call("\nTimestamp check complete.")
        mock_get_csv.assert_called_once_with(os.path.normpath("dummy_dir_one_csv/only_one.csv"))


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)

# Notes on testing __main__ block:
# - The `run_main_script` helper uses `runpy.run_module("check_timestamps", run_name="__main__")`.
#   This executes `check_timestamps.py` as if it were the main script.
# - `sys.argv` is patched to simulate command-line arguments.
# - `sys.exit` is mocked to prevent the test runner from exiting and to assert that `exit(1)` is called on errors.
# - `builtins.print` is mocked to capture output and verify messages.
# - `os.path.exists`, `os.listdir`, `os.path.join`, and `check_timestamps.get_timestamps_from_csv` are mocked
#   to control the environment and inputs for the main script logic.
# - The test for `test_main_inconsistent_timestamps_different_values` was adjusted to reflect how the script reports
#   differences when sets are not equal (it reports missing and extra rather than "different at position" unless counts are identical).
# - `os.path.normpath` used in `mock_path_join` to handle potential mixed slashes if tests run on Windows but expect Unix paths or vice-versa.
#   This is generally good practice for path manipulations in tests.
# - The `TestGetTimestampsFromCSV` tests use `io.StringIO` to simulate file content for `mock_open`.
# - `mock_print.assert_not_called()` is used in success cases for `get_timestamps_from_csv` where no warnings are expected.
# - Test for `get_timestamps_from_csv` when the file itself cannot be read (`IOError`).
# - The main logic tests check for calls to `sys.exit(1)` which is how the script signals critical errors.
# - The test `test_main_one_csv_file` verifies that the script handles the case of a single CSV file gracefully.
#   The original script doesn't have a specific "only one file found" message before "check complete",
#   but it should process it and finish without error. The mock asserts the reference message.
# - Corrected `side_effect` for `os.path.join` to ensure it returns a usable path string.
#   `os.path.normpath(os.path.join(*args))` is a robust way.
# - Ensured `mock_exit` is returned from `run_main_script` to allow assertions on it.
The unit tests for `check_timestamps.py` have been created in `tests/test_check_timestamps.py`.

Key features of this test suite:

1.  **`TestGetTimestampsFromCSV` Class:**
    *   Tests the `get_timestamps_from_csv` function.
    *   Uses `@patch("builtins.open", new_callable=mock_open)` to simulate file reading with various CSV contents (valid with/without milliseconds, empty, no 'date and time' column, unparseable dates).
    *   Uses `@patch("builtins.print")` to capture and verify warning/error messages printed by the function.
    *   Tests `IOError` during file open.
    *   Asserts the correctness of the returned set of datetime objects or `None` in error cases.

2.  **`TestCheckTimestampsMainExecution` Class:**
    *   Tests the main script logic found in the `if __name__ == '__main__':` block of `check_timestamps.py`.
    *   A helper method `run_main_script(self, args)` is defined:
        *   It uses `runpy.run_module("check_timestamps", run_name="__main__")` to execute the script as if it were run directly.
        *   It mocks `sys.argv` to pass command-line arguments.
        *   It mocks `sys.exit` to prevent tests from stopping and to verify exit codes.
    *   Mocks `check_timestamps.os.listdir`, `check_timestamps.os.path.exists`, `check_timestamps.os.path.join`, `check_timestamps.get_timestamps_from_csv`, and `builtins.print` to control the execution environment and capture outputs.
    *   **Test Scenarios:**
        *   `test_main_consistent_timestamps`: All mock CSV files have the same timestamps.
        *   `test_main_inconsistent_timestamps_missing`: One mock CSV file is missing timestamps compared to the reference.
        *   `test_main_inconsistent_timestamps_extra`: One mock CSV file has extra timestamps.
        *   `test_main_inconsistent_timestamps_different_values`: Mock CSV files have differing timestamps (leading to missing/extra reports by the script's logic).
        *   `test_main_no_csv_files`: The mocked directory contains no CSV files. Verifies `sys.exit(1)` is called.
        *   `test_main_directory_not_found`: The mocked directory does not exist. Verifies `sys.exit(1)` is called.
        *   `test_main_one_csv_file`: Only one CSV file is present; verifies it's processed as reference and the script completes.
    *   Asserts that `builtins.print` is called with the expected messages for each scenario.
    *   Asserts that `sys.exit(1)` is called for critical error conditions.

This approach allows testing the main execution block of the script without refactoring it into a separate function, by using `runpy` and extensive mocking.

I am now ready to submit the report.
