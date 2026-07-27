"""
Main routine--creates Patient Match Reviewer GUI.
"""

import argparse
import logging
import os

import wx.adv

from src.patientmatchreviewer.common import get_logging_directory, resource_path
from src.patientmatchreviewer.my_logging import setup_logging
from src.patientmatchreviewer.reviewer_gui import ReviewerGui
from src.patientmatchreviewer.splash import MySplashScreen


def main():
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="A GUI-based tool to retrieve All of Us participant data using the InSite API."
    )
    parser.add_argument(
        "--log-level", type=str, help="INFO, DEBUG, etc.", default="INFO"
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Name of wobbler file to review.",
        default="",
    )

    # Find directory in which we're allowed to write log file.
    logging_dir: str | None = get_logging_directory(suggested_dir=os.getcwd())

    if logging_dir:
        log: logging.Logger = setup_logging(
            log_filename=os.path.join(logging_dir, "patientmatchreviewer.log")
        )
        args = parser.parse_args()

        if args.log_level and args.log_level in [
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL",
        ]:
            log.setLevel(args.log_level)

        log.info("App starting.")

        # Display splash screen.
        app: wx.App = wx.App(redirect=False)
        splash = MySplashScreen(resource_path("pictures/UCSD_school_of_medicine.png"))
        splash.Show()
        app.Yield()

        # Create the GUI.
        log.info("Instantiating ApiGui object.")
        gui: ReviewerGui = ReviewerGui(log, args.file)

        try:
            splash.Destroy()
        except RuntimeError:
            pass

        app.MainLoop()


if __name__ == "__main__":
    main()
