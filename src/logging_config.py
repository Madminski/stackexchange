import configparser
import logging
import os
import sys


def setup_logging():
    # Read the configuration file
    config = configparser.ConfigParser()
    config.read("/mnt/d/stackexchange/config.ini")

    log_format = "%(asctime)s - %(filename)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Get the log directory, filename, and level from the configuration file
    log_directory = config.get("logging", "log_directory")
    log_filename = config.get("logging", "log_filename")
    log_level = config.get("logging", "log_level")

    # Convert the log level string to the corresponding logging level constant
    log_level = getattr(logging, log_level.upper())

    # Create the log directory if it doesn't exist
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    log_file_path = os.path.join(log_directory, log_filename)

    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Set up console handler (for output to terminal)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(log_format, datefmt=date_format)
    console_handler.setFormatter(console_formatter)

    # Set up file handler (for output to log file)
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter(log_format, datefmt=date_format)
    file_handler.setFormatter(file_formatter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    return root_logger
