"""
Allows other projects to easily use logging.
"""

import inspect
import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Union


def setup_logging(log_filename: Union[str, None] = None) -> logging.Logger:
    """

    Parameters
    ----------
    log_filename : Optional str Desired name of the log file.
                    Can be either a full path or just a filename.

    Returns
    -------
    logger : logging.Logger object to be used in calling routine.

    """
    #       Clear up any old stuff.
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    if not isinstance(log_filename, str):
        #   If user didn't supply a filename, create it with the calling module's name.
        #   (Don't use calling >function<, as it will likely be '__init__', which tells us nothing.
        frame_records = inspect.stack()[1]
        calling_module = inspect.getmodulename(frame_records[1])
        log_filename = f"AoU_{calling_module}.log"

    # Ensure the path to the log file exists.
    file_path: Path = Path(log_filename)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    #   Create the logger object named after the filename.
    just_the_filename = os.path.splitext(os.path.basename(log_filename))[0]
    logger = logging.getLogger(just_the_filename)
    console_handler = logging.StreamHandler(sys.stdout)
    console_format = logging.Formatter("%(module)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(console_format)

    # New log for every day; discard logs > 30 days old.
    logfile_handler = logging.handlers.TimedRotatingFileHandler(
        filename=log_filename,
        when="D",
        interval=1,
        backupCount=30,
        encoding="utf-8",
        delay=False,
    )
    logfile_format = logging.Formatter(
        fmt="%(asctime)s - %(module)s - %(funcName)s - %(levelname)s - %(message)s"
    )
    logfile_handler.setFormatter(logfile_format)

    logger.addHandler(console_handler)
    logger.addHandler(logfile_handler)
    logger.setLevel(logging.INFO)
    return logger
