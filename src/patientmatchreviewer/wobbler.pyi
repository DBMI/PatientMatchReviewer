import logging
from enum import StrEnum
from typing import NamedTuple

import pandas

class MatchDecision(StrEnum):
    """
    Enum class for recording reviewer's decision.
    """

    MATCH = "MATCH"
    NO_MATCH = "NO_MATCH"
    UNSURE = "UNSURE"
    NONE = ""

class PatientComparison(NamedTuple):
    """
    One row of the DataFrame
    """

    ADDR1_AOU: str
    ADDR1_OMOP: str
    ADDR1_SCORE: int
    DOB_AOU: str
    DOB_OMOP: str
    DOB_SCORE: int
    FAMILY_NAME_AOU: str
    FAMILY_NAME_OMOP: str
    FAMILY_NAME_SCORE: int
    GIVEN_NAME_AOU: str
    GIVEN_NAME_OMOP: str
    GIVEN_NAME_SCORE: int
    MATCH: str
    MRN: str
    OMOP_ID: str
    PHONE1_AOU: str
    PHONE1_OMOP: str
    PHONE1_SCORE: int
    PHONE2_AOU: str
    PHONE2_OMOP: str
    PHONE2_SCORE: int
    PMI_ID: str
    TOTAL_SCORE: int

class Wobbler:
    def __build_header(self) -> PatientComparison: ...
    def read_wobbler_file(match_file: str, log: logging.Logger) -> pandas.DataFrame: ...
    def __write_row(match_file: str, row: PatientComparison) -> bool: ...
    def write_wobbler_file(
        match_file: str, df: pandas.DataFrame, log: logging.Logger
    ) -> bool: ...
