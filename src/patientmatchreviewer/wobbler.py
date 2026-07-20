import logging
import os
import re
from enum import StrEnum
from pathlib import Path
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


# Define using class syntax with type hints
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
    """
    Static class for reading/writing "wobbler" files, which
    record cases where we can't automatically decide whether
    the patient in AoU is the same person as described in OMOP.

    "wobbler" files are machine-written by our AoU code, and can be
    either edited by hand or using the ReviewerGui app.
    They are then re-read (including the human decisions) as the AoU code resumes.

    Attributes:
    ----------
    no public attributes

    Methods
    -------
    read_wobbler_file()
    write_wobble_file()
    """

    @staticmethod
    def __build_header() -> PatientComparison:
        d: dict = {
            "ADDR1_AOU": "addr1_aou",
            "ADDR1_OMOP": "addr1_omop",
            "ADDR1_SCORE": "addr1_score",
            "DOB_AOU": "dob_aou",
            "DOB_OMOP": "dob_omop",
            "DOB_SCORE": "dob_score",
            "FAMILY_NAME_AOU": "family_name_aou",
            "FAMILY_NAME_OMOP": "family_name_omop",
            "FAMILY_NAME_SCORE": "family_name_score",
            "GIVEN_NAME_AOU": "given_name_aou",
            "GIVEN_NAME_OMOP": "given_name_omop",
            "GIVEN_NAME_SCORE": "given_name_score",
            "MATCH": "",
            "MRN": "mrn",
            "OMOP_ID": "omop_id",
            "PHONE1_AOU": "phone1_aou",
            "PHONE1_OMOP": "phone1_omop",
            "PHONE1_SCORE": "phone1_score",
            "PHONE2_AOU": "phone2_aou",
            "PHONE2_OMOP": "phone2_omop",
            "PHONE2_SCORE": "phone2_score",
            "PMI_ID": "pmi_id",
            "TOTAL_SCORE": "total_score",
        }
        return PatientComparison(**d)

    @staticmethod
    def read_wobbler_file(match_file: str, log: logging.Logger) -> pandas.DataFrame:
        """
        Just read in the file into a pandas DataFrame. Leave database merging for the calling routine.

        Parameters
        ----------
        match_file: str                     Full path of file to read.
        log: logging.Logger                 Logging object

        Returns
        -------
        df: pandas.DataFrame

        """
        log.info("Reading manual matches from '%s'", match_file)

        # Initialize dataframe.
        column_names: list = [
            "ADDR1_AOU",
            "ADDR1_OMOP",
            "ADDR1_SCORE",
            "DOB_AOU",
            "DOB_OMOP",
            "DOB_SCORE",
            "FAMILY_NAME_AOU",
            "FAMILY_NAME_OMOP",
            "FAMILY_NAME_SCORE",
            "GIVEN_NAME_AOU",
            "GIVEN_NAME_OMOP",
            "GIVEN_NAME_SCORE",
            "MATCH",
            "MRN",
            "OMOP_ID",
            "PHONE1_AOU",
            "PHONE1_OMOP",
            "PHONE1_SCORE",
            "PHONE2_AOU",
            "PHONE2_OMOP",
            "PHONE2_SCORE",
            "PMI_ID",
            "TOTAL_SCORE",
        ]
        data_rows: list = []

        # Separator string
        sep: str = "--------"
        num_separators_found: int = 0

        # Detect selected match/no match/unsure.
        # https://fsymbols.com/signs/tick/
        decision_marks: str = r".xXyY✓✔√✅❎☒☑✕✗✘✖❌"

        # Are we inside a record (between two separator strings)?
        in_record: bool = False

        try:
            with open(match_file, "r", encoding="utf-8-sig", newline="") as file:
                for line in file:
                    # The separator marks the end of a record & the start of a new record.
                    if line.startswith(sep):
                        num_separators_found += 1

                        # Don't start looking for data until we've seen TWO separator strings.
                        if num_separators_found < 2:
                            continue

                        # If already IN a record, then the separator marks the end of the record.
                        if in_record:
                            # Once we've read the whole record, record this possible match.
                            new_row: list = [
                                addr1_aou,
                                addr1_omop,
                                addr1_score,
                                dob_aou,
                                dob_omop,
                                dob_score,
                                family_name_aou,
                                family_name_omop,
                                family_name_score,
                                given_name_aou,
                                given_name_omop,
                                given_name_score,
                                match,
                                mrn,
                                omop_id,
                                phone1_aou,
                                phone1_omop,
                                phone1_score,
                                phone2_aou,
                                phone2_omop,
                                phone2_score,
                                pmi_id,
                                total_score,
                            ]
                            data_rows.append(new_row)
                            in_record = False
                            continue

                    # We're starting a new record--reset the parser.
                    in_record = True
                    addr1_aou: str = ""
                    addr1_omop: str = ""
                    addr1_score: int = 0
                    dob_aou: str = ""
                    dob_omop: str = ""
                    dob_score: int = 0
                    family_name_aou: str = ""
                    family_name_omop: str = ""
                    family_name_score: int = 0
                    given_name_aou: str = ""
                    given_name_omop: str = ""
                    given_name_score: int = 0
                    match: MatchDecision = MatchDecision.NONE
                    mrn: str = ""
                    omop_id: str = ""
                    phone1_aou: str = ""
                    phone1_omop: str = ""
                    phone1_score: int = 0
                    phone2_aou: str = ""
                    phone2_omop: str = ""
                    phone2_score: int = 0
                    pmi_id: str = ""
                    total_score: int = 0

                    # Don't start looking for data until we've seen TWO separator strings.
                    if num_separators_found < 2:
                        continue

                    # Split on MORE than one space (or on ":").
                    # This way, "123 Maple Street" stays together
                    # and "Total Score: 123" gets split.
                    # CAUTION: Don't believe automated hint that "?:" on next line is unnecessary.
                    tokens_raw: list = re.split(r"(\s{2,}|:)", line)

                    # Discard empty strings & strip newlines.
                    tokens: list = [s.strip("\r") for s in tokens_raw if s]

                    match len(tokens):
                        case 0:
                            continue

                        case 1:
                            token0: str = tokens[0].upper().replace("_", " ")

                            # Maybe it's a match statement.
                            if "NO MATCH" in token0 and any(
                                mark in line for mark in decision_marks
                            ):
                                match = MatchDecision.NO_MATCH
                            elif "MATCH" in token0 and any(
                                mark in line for mark in decision_marks
                            ):
                                match = MatchDecision.MATCH
                            elif "UNSURE" in token0 and any(
                                mark in line for mark in decision_marks
                            ):
                                match = MatchDecision.UNSURE

                            continue

                        case _:
                            token0: str = tokens[0].upper().replace("_", " ")

                            # Perhaps a statement like "MRN      123421234"
                            match token0:

                                case "ADDR1":
                                    addr1_aou = tokens[1]

                                    if len(tokens) > 3:
                                        addr1_omop = tokens[2]
                                        addr1_score = tokens[3]

                                    continue

                                case "DOB":
                                    dob_aou = tokens[1]

                                    if len(tokens) > 3:
                                        dob_omop = tokens[2]
                                        dob_score = tokens[3]

                                    continue

                                case "FIRST":
                                    given_name_aou = tokens[1]

                                    if len(tokens) > 3:
                                        given_name_omop = tokens[2]
                                        given_name_score = tokens[3]

                                    continue

                                case "LAST":
                                    family_name_aou = tokens[1]

                                    if len(tokens) > 3:
                                        family_name_omop = tokens[2]
                                        family_name_score = tokens[3]
                                    continue

                                case "MRN":
                                    mrn = tokens[1]
                                    continue

                                case "OMOP ID":
                                    omop_id = tokens[1]
                                    continue

                                case "PHONE1":
                                    phone1_aou = tokens[1]

                                    if len(tokens) > 3:
                                        phone1_omop = tokens[2]
                                        phone1_score = tokens[3]

                                    continue

                                case "PHONE2":
                                    phone2_aou = tokens[1]

                                    if len(tokens) > 3:
                                        phone2_omop = tokens[2]
                                        phone2_score = tokens[3]

                                    continue

                                case "PMI ID":
                                    pmi_id = tokens[1]
                                    continue

                                case "TOTAL SCORE":
                                    total_score = tokens[1]
                                    continue

                    continue

            # Convert list to dataframe.
            df: pandas.DataFrame = pandas.DataFrame(data_rows, columns=column_names)
            return df

        except FileNotFoundError as e:
            log.exception(f"File {match_file} not found.")
            raise

    @staticmethod
    def __write_row(match_file: str, row: PatientComparison) -> bool:
        """
            Write out one row from a wobbler file.

        Parameters
        ----------
        match_file: str                     Full path of file to write.
        row: PatientComparison
        log: logging.Logger                 Logging object

        Returns
        -------
        success: bool
        """

        out: str = ""
        out += "----------------------------------------------" + os.linesep
        out += os.linesep
        out += "PMI_ID      {0:>15}".format(row.PMI_ID)
        out += os.linesep
        out += "OMOP ID     {0:>15}".format(row.OMOP_ID)
        out += os.linesep
        out += "MRN         {0:>15}".format(row.MRN)
        out += os.linesep
        out += os.linesep
        out += "{0:10}  {1:30}   {2:30}   {3:>5}".format(
            "first", row.GIVEN_NAME_AOU, row.GIVEN_NAME_OMOP, row.GIVEN_NAME_SCORE
        )
        out += os.linesep
        out += "{0:10}  {1:30}   {2:30}   {3:>5}".format(
            "last", row.FAMILY_NAME_AOU, row.FAMILY_NAME_OMOP, row.FAMILY_NAME_SCORE
        )
        out += os.linesep
        out += "{0:10}  {1:30}   {2:30}   {3:>5}".format(
            "dob", row.DOB_AOU, row.DOB_OMOP, row.DOB_SCORE
        )
        out += os.linesep
        out += "{0:10}  {1:30}   {2:30}   {3:>5}".format(
            "addr1", row.ADDR1_AOU, row.ADDR1_OMOP, row.ADDR1_SCORE
        )
        out += os.linesep
        out += "{0:10}  {1:30}   {2:30}   {3:>5}".format(
            "phone1", row.PHONE1_AOU, row.PHONE1_OMOP, row.PHONE1_SCORE
        )
        out += os.linesep
        out += "{0:10}  {1:30}   {2:30}   {3:>5}".format(
            "phone2", row.PHONE2_AOU, row.PHONE2_OMOP, row.PHONE2_SCORE
        )
        out += os.linesep
        out += os.linesep
        out += "Total Score: {0}".format(row.TOTAL_SCORE)
        out += os.linesep
        out += os.linesep
        out += "Check ☑ ONE of these lines:"
        out += os.linesep

        match row.MATCH:
            case MatchDecision.MATCH:
                out += "☑ MATCH"
                out += os.linesep
                out += "☐ NO_MATCH"
                out += os.linesep
                out += "☐ UNSURE"
                out += os.linesep

            case MatchDecision.NO_MATCH:
                out += "☐ MATCH"
                out += os.linesep
                out += "☑ NO_MATCH"
                out += os.linesep
                out += "☐ UNSURE"
                out += os.linesep

            case MatchDecision.UNSURE:
                out += "☐ MATCH"
                out += os.linesep
                out += "☐ NO_MATCH"
                out += os.linesep
                out += "☑ UNSURE"
                out += os.linesep

            # This will only be used for the file header.
            case MatchDecision.NONE:
                out += "☐ MATCH"
                out += os.linesep
                out += "☐ NO_MATCH"
                out += os.linesep
                out += "☐ UNSURE"
                out += os.linesep

        with open(match_file, "a", encoding="utf8") as outfile:
            outfile.write(out)

        return True

    @staticmethod
    def write_wobbler_file(
        match_file: str, df: pandas.DataFrame, log: logging.Logger
    ) -> bool:
        """
            Write a wobbler file from a pandas DataFrame.

        Parameters
        ----------
        match_file: str                     Full path of file to write.
        df : pandas.DataFrame               Contains the comparison information
        log: logging.Logger                 Logging object

        Returns
        -------
        success: bool
        """
        log.info("Writing manual matches to '%s'", match_file)

        # Ensure directory exists.
        file_path: Path = Path(match_file)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # But get rid of existing file.
        file_path.unlink(missing_ok=True)

        # Sort in descending order by TOTAL_SCORE.
        df.sort_values(by="TOTAL_SCORE", ascending=False, inplace=True)

        num_records_written: int = 0

        header_obj: PatientComparison = Wobbler.__build_header()
        Wobbler.__write_row(match_file, header_obj)

        for row in df.itertuples(index=False, name="PatientComparison"):
            Wobbler.__write_row(match_file, row)
            num_records_written += 1

        log.info("Wrote %d matches to '%s'", num_records_written, match_file)
        return True
