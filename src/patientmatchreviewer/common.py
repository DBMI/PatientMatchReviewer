"""
Collection of static utility methods.
"""
import errno
import logging
import os
import re
import sys
import tempfile
from contextlib import nullcontext
from pathlib import Path
from configparser import ConfigParser, ExtendedInterpolation

import pywintypes
import win32api


def ensure_path_possible(filename: str, log: logging.Logger) -> bool:
    """
    Tests to ensure the filename provided can actually be created.

    Parameters
    ----------
    filename: str           File we propose to create
    log: logging.Logger     To assist in debugging

    Returns
    -------
    bool
    """
    log.debug(f"Checking path '{filename}' exists.")
    directory_name: str = os.path.dirname(filename)
    log.debug(f"Checking directory '{directory_name}' exists.")
    directory_path = Path(directory_name)

    # Does this directory already exist?
    if os.path.exists(directory_path):
        return True

    try:
        directory_path.mkdir(parents=True, exist_ok=True)
        log.debug(f"Directory '{directory_name}' created.")

        # OK, we CAN create it, so now delete it.
        # (Helps when we're calling this method with every new
        os.rmdir(directory_name)
        return True
    except OSError as e:
        log.error(f"Error ensuring directory '{directory_name} because: {e}")
        print(f"Error ensuring directory '{directory_name}': {e}")
        return False


def get_base_path() -> str:
    """
    Adapts to running either in development OR in executable format.

    Returns
    -------
    base_path: str      Where to find included data or image files.
    """
    base_path: str

    if getattr(sys, "frozen", False):  # pragma: no cover
        base_path = sys._MEIPASS  # pylint: disable=W0212
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return base_path


def get_config(log: logging.Logger, config_file: str = None) -> ConfigParser:
    """
    Reads config file.

    Parameters
    ----------
    log: logging.Logger object
    config_file: str                    Optional

    Returns
    -------
    config parser object
    """

    if not config_file:
        config_file = get_default_ini_path()

    log.info(f"Reading config from {config_file}.")

    if not (os.path.exists(config_file) and os.path.isfile(config_file)):
        log.info(f"Config file {config_file} not found.")
        __make_config(config_file, log)

    config = ConfigParser(interpolation=ExtendedInterpolation())
    config.read(config_file)
    return config


def get_default_ini_path() -> str:
    """
    Where to look for config file.

    Returns
    -------
    default_path: str
    """
    return str(os.path.join(os.getcwd(), "config.ini"))


def get_exe_path() -> str:
    """
    Where to look for the .exe file information

    Returns
    -------
    exe_path: str
    """
    exe_path: str

    if getattr(sys, "frozen", False):  # pragma: no cover
        exe_path = sys.executable
    else:
        exe_path = os.path.abspath(__file__)

    return exe_path


def get_exe_version(log: logging.Logger) -> str:
    """
    Get the version of the executable, either from the .exe OR the version.txt files.

    Parameters
    ----------
    log

    Returns
    -------
    version: str
    """
    exe_path: str = get_exe_path()
    log.debug("Found exe path: {exe_path}.")

    try:  # pragma: no cover
        # Get the full path to the executable.
        log.debug(f"Getting abspath from {exe_path}.")
        full_path = os.path.abspath(exe_path)

        # Get the file version information.
        log.debug(f"Requesting version info from {full_path}.")
        info = win32api.GetFileVersionInfo(full_path, "\\")
        log.debug(f"Version info: {info}.")

        # Extract the major, minor, build, and private parts of the version.
        ms = info["FileVersionMS"]
        ls = info["FileVersionLS"]

        version = (
            f"{win32api.HIWORD(ms)}."
            f"{win32api.LOWORD(ms)}."
            f"{win32api.HIWORD(ls)}."
            f"{win32api.LOWORD(ls)}"
        )
        return version
    except pywintypes.error as e:  # pylint: disable=no-member
        ver_from_file: str = parse_version_file()

        if ver_from_file:
            return ver_from_file

        print(f"Error getting version for {exe_path}: {e}")  # pragma: no cover
        return ""  # pragma: no cover


def get_logging_directory(suggested_dir: str) -> str | None:
    """
    If suggested directory is writable, use that. Otherwise, return system temp directory (or None).

    Parameters
    ----------
    suggested_dir: str

    Returns
    -------
    str | None
    """
    if is_writable(path_to_test=suggested_dir):
        return suggested_dir

    return get_temp_directory()


# https://stackoverflow.com/a/847866/20241849
def get_temp_directory() -> str | None:
    """
    Uses tempfile's capability to find system's temp directory. Tries "C:\tmp" as backup.

    Returns
    -------
    temp_directory : str | None
    """
    temp_directory: str = tempfile.gettempdir()

    if is_writable(path_to_test=temp_directory):
        return temp_directory
    else:
        if is_writable(path_to_test="C:\tmp"):
            return "C:\tmp"
        else:
            return None

# https://stackoverflow.com/a/25868839/20241849
def is_writable(path_to_test: str) -> bool:
    """
    Tests path to see if it is writable.

    Parameters
    ----------
    path_to_test : str

    Returns
    -------
    success : bool
    """
    try:
        testfile = tempfile.TemporaryFile(dir=path_to_test)
        testfile.close()
    except OSError as e:
        if e.errno == errno.EACCES:  # 13
            return False
        e.filename = path_to_test
    return True


def __make_config(config_file: str, log: logging.Logger) -> None:
    """
    Initializes config file with default values.

    Parameters
    ----------
    config_file: str        Full path to config.ini file
    log

    Returns
    -------
    None
    """
    cwd: str = os.getcwd()
    config: ConfigParser = ConfigParser()
    config["Settings"] = {
        "manual_decision_file_path": r"F:\dbmi.data\manual_decision_file.txt",
    }

    with open(config_file, "w", encoding="utf-8") as configfile:
        log.info(f"Writing config to file {config_file}.")
        config.write(configfile)


def parse_version_file() -> str:
    """
    Parse the version file to extract the ProductVersion string.

    Returns
    -------
    version: str
    """
    file_path: str = resource_path("version_info.txt")

    with open(file_path, "r", encoding="utf-8") as version_file:
        file_content = version_file.read()
        pattern: str = r"ProductVersion',\s'(?P<version>\d+\.\d+\.\d+)"
        match = re.search(pattern, file_content)

        if match:
            return match.group("version")

        return ""  # pragma: no cover


# https://stackoverflow.com/a/13790741/20241849
def resource_path(relative_path: str) -> str:
    """
    Given name of resource, builds absolute path to resource, works for dev and PyInstaller.

    Parameters
    ----------
    relative_path: str

    Returns
    -------
    base_path: str
    """
    if getattr(sys, "frozen", False):  # pragma: no cover
        # Running in a PyInstaller bundle.
        base_path = sys._MEIPASS  # pylint: disable=W0212
    else:
        # Running in a normal Python environment.
        base_path = os.getcwd()

    return str(os.path.join(base_path, relative_path))


def write_config(config: ConfigParser, log: logging.Logger, config_file: str = "") -> None:
    """
    Initializes config file with default values.

    Parameters
    ----------
    config: ConfigParser
    log
    config_file: str        Full path to config.ini file

    """
    if not config_file:
        config_file = get_default_ini_path()

    with open(config_file, "w", encoding="utf-8") as configfile:
        log.info(f"Writing config to file {config_file}.")
        config.write(configfile)
