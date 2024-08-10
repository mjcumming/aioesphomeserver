"""
This module provides logging utilities with color-coded log levels for better visibility.

It defines functions and mappings to format log messages with specific colors and levels,
making it easier to distinguish between different types of log entries in the output.
"""

import logging  # Ensure logging is imported since it's used in LOG_LEVEL_MAPPING

# Mapping standard logging levels to your custom levels
LOG_LEVEL_MAPPING = {
    logging.CRITICAL: 1,
    logging.ERROR: 1,
    logging.WARNING: 2,
    logging.INFO: 3,
    logging.DEBUG: 5,
}

LOG_LEVEL_COLORS = [
    "",           # NONE
    "\033[1;31m", # ERROR (bold red)
    "\033[0;33m", # WARNING (yellow)
    "\033[0;32m", # INFO (green)
    "\033[0;35m", # CONFIG (magenta)
    "\033[0;36m", # DEBUG (cyan)
    "\033[0;37m", # VERBOSE (gray)
    "\033[0;38m", # VERY_VERBOSE (white)
]

LOG_LEVEL_LETTERS = [
    "",    # NONE
    "E",   # ERROR
    "W",   # WARNING
    "I",   # INFO
    "C",   # CONFIG
    "D",   # DEBUG
    "V",   # VERBOSE
    "VV",  # VERY_VERBOSE
]

LOG_RESET = "\033[0m"

def format_log(level, tag, line_number, message):
    """
    Formats a log message with color and additional context.

    Args:
        level (int): The logging level (e.g., logging.INFO, logging.ERROR).
        tag (str): A tag for categorizing the log message.
        line_number (int): The line number where the log originated.
        message (str): The message to log.

    Returns:
        str: The formatted log message with color and context.
    """
    # Map the level to your custom level indices
    custom_level = LOG_LEVEL_MAPPING.get(level, 3)  # Default to INFO level

    color = LOG_LEVEL_COLORS[custom_level]
    letter = LOG_LEVEL_LETTERS[custom_level]
        
    return f"{color}[{letter}][{tag}:{line_number}]: {message}{LOG_RESET}"
