import csv  # Import the csv module to work with CSV files.
import os  # Import os to create directories.
from datetime import datetime  # Import datetime to get the current timestamp.

class SecurityLogger:  # Defines the class responsible for logging security events.
    def __init__(self, log_dir='logs'):  # The constructor method.
        """Initializes the logger, creating the log directory and file if they don't exist."""
        os.makedirs(log_dir, exist_ok=True)  # Create the log directory (e.g., 'logs/') if it's not already there.
        # Create a unique log filename for each day to keep logs organized.
        log_filename = f"security_log_{datetime.now().strftime('%Y-%m-%d')}.csv"  # e.g., "security_log_2023-10-27.csv"
        self.log_path = os.path.join(log_dir, log_filename)  # Construct the full path to the log file.
        
        # --- Write Header Row to New Files ---
        # This ensures the CSV file has column titles, but only does it once when the file is first created.
        if not os.path.exists(self.log_path):  # Check if the log file for today does not exist yet.
            with open(self.log_path, 'w', newline='') as f:  # Open the file in write mode ('w').
                writer = csv.writer(f)  # Create a CSV writer object.
                writer.writerow(['Timestamp', 'Event', 'Name', 'Details'])  # Write the header row.

    def log_event(self, event_type, name="N/A", details=""):  # Method to log a single event.
        """Logs an event to the daily CSV file."""
        # --- Argument Explanations ---
        # event_type (str): Type of event (e.g., 'KNOWN_PERSON_ENTRY', 'UNKNOWN_PERSON_ALERT').
        # name (str): The name of the person involved. Defaults to "N/A".
        # details (str): Any additional details about the event. Defaults to an empty string.

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Get the current time as a formatted string.
        with open(self.log_path, 'a', newline='') as f:  # Open the log file in append mode ('a') to add a new line.
            writer = csv.writer(f)  # Create a CSV writer object.
            writer.writerow([timestamp, event_type, name, details])  # Write the new event data as a row in the CSV.