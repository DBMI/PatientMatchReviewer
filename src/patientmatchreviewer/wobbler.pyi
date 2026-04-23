import logging
import pandas
from enum import StrEnum


class MatchDecision(StrEnum):
    """
    Enum class for recording reviewer's decision.
    """
    MATCH = "MATCH"
    NO_MATCH = "NO_MATCH"
    UNSURE = "UNSURE"


class Wobbler():

    def read_wobbler_file(match_file: str, log: logging.Logger) -> pandas.DataFrame: ...
    def write_wobbler_file(match_file: str, df: pandas.DataFrame, log: logging.Logger) -> None: ...
