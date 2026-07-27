"""
Module: Contains class ReviewerGui, which creates the GUI
        users can use to review patient matching data.
"""

import logging
import os
from configparser import ConfigParser
from pathlib import Path
from tkinter import filedialog
from datetime import datetime
import pandas
import wx
import wx.adv

from patientmatchreviewer.common import get_config, resource_path, write_config
from patientmatchreviewer.wobbler import MatchDecision, Wobbler


class ReviewerGui(wx.Dialog):
    """
    GUI for reviewing patient matching data.

    Attributes:
    ----------
    no public attributes

    Methods
    -------
    no public methods
    """

    def __init__(self, log: logging.Logger, filename: str = "") -> None:
        """
        Initialize the GUI.

        Parameters
        ----------
        file: str                    Possible patient matching data
        """

        self.__log: logging.Logger = log
        self.__config: ConfigParser = get_config(self.__log)
        self.__log.info("Instantiating Reviewer Gui.")
        wx.Dialog.__init__(
            self,
            parent=None,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
            size=wx.Size(600, 650),
            title="Review patient matching data data",
        )  # pylint: disable=no-member

        sizer: wx.BoxSizer = wx.BoxSizer(wx.VERTICAL)
        self.SetBackgroundColour(wx.Colour(255, 255, 255))

        # Set up this panel.
        self.__my_panel: wx.Panel = wx.Panel(self)
        self.__my_panel.Font = wx.Font(
            14,
            family=wx.FONTFAMILY_ROMAN,
            style=wx.FONTSTYLE_NORMAL,
            weight=wx.FONTWEIGHT_NORMAL,
        )

        # Create grid.
        self.__my_grid: wx.GridBagSizer = wx.GridBagSizer(hgap=5, vgap=5)

        # Add title.
        self.__control_row: int = 0
        self.__add_title(label="Review possible patient matches")

        # Where to find image files.
        self.__image_directory: str = resource_path(r"pictures")
        #
        #   LOAD BUTTON
        #
        self.df: pandas.DataFrame
        self.__add_load_button()
        # Leave empty row.
        self.__control_row += 1

        # Keep track of row in dataframe.
        self.__row: int = 0
        #
        #   HEADER INFORMATION
        #
        self.__text_controls: dict[str, wx.StaticText] = {}
        self.__add_single_info(data_field="PMI_ID")
        self.__add_single_info(data_field="OMOP_ID")
        self.__add_single_info(data_field="MRN")
        #
        #   RECORD COMPARISON
        #
        self.__add_header_row()
        self.__add_comparison_row(data_field="GIVEN_NAME")
        self.__add_comparison_row(data_field="FAMILY_NAME")
        self.__add_comparison_row(data_field="DOB")
        self.__add_comparison_row(data_field="ADDR1")
        self.__add_comparison_row(data_field="PHONE1")
        self.__add_comparison_row(data_field="PHONE2")
        self.__add_single_info(data_field="TOTAL_SCORE")
        #
        #   DECISION BUTTONS
        #
        self.__radio_box: wx.RadioBox
        self.__add_decision_radiobuttons()
        #
        #   NAVIGATION BUTTONS
        self.__left_button: wx.Button
        self.__right_button: wx.Button
        self.__add_navigation_buttons()
        #
        #   SHOW PROGRESS
        #
        self.__progress_text: wx.StaticText
        self.__progress_gauge: wx.Gauge
        self.__add_progress_info()
        #
        #   SAVE/CANCEL BUTTONS
        #
        self.__save_button: wx.Button
        self.__add_save_and_cancel_buttons()

        # Connect grid sizer to panel.
        self.__my_panel.SetSizerAndFit(self.__my_grid)

        # Do this before closing.
        self.Bind(wx.EVT_CLOSE, self.__on_close)

        # Finish at Frame level.
        sizer.Add(self.__my_panel, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        self.SetSizer(sizer)
        self.Layout()
        self.Fit()

        if filename and len(filename) > 0:
            self.__load_file(filename)

        self.ShowModal()

    def __add_comparison_row(self, data_field: str) -> None:
        """
            Create comparison row like "FAMILY NAME:    Smith   Smyth   79"

        Parameters
        ----------
        data_field:     Root name for what the dataframe calls these three data elements
                        For example, if "dob", the dataframe should contain columns
                                "DOB_AOU"
                                "DOB_OMOP"
                                "DOB_SCORE"
        Returns
        -------
        none
        """
        # Build grid to hold row's objects.
        [containing_panel, row_grid] = self.__build_row(data_field=data_field)
        #
        #   The element name ("ADDR1")
        #
        control_label: wx.StaticText = wx.StaticText(
            containing_panel, style=wx.TRANSPARENT_WINDOW, label=data_field
        )
        row_grid.Add(control_label, pos=(1, 0), flag=wx.ALIGN_LEFT, border=5)
        #
        #   The AOU value ("ADDR1 AOU")
        #
        control_label_aou: wx.StaticText = wx.StaticText(
            containing_panel, style=wx.TRANSPARENT_WINDOW, label="AOU"
        )
        row_grid.Add(control_label_aou, pos=(1, 1), flag=wx.ALIGN_LEFT, border=5)
        self.__text_controls[data_field + "_AOU"] = control_label_aou
        #
        #   The OMOP value ("ADDR1 OMOP")
        #
        control_label_omop: wx.StaticText = wx.StaticText(
            containing_panel, style=wx.TRANSPARENT_WINDOW, label="OMOP"
        )
        row_grid.Add(control_label_omop, pos=(1, 2), flag=wx.ALIGN_LEFT, border=5)
        self.__text_controls[data_field + "_OMOP"] = control_label_omop
        #
        #   The score ("ADDR1 SCORE")
        control_label_score: wx.StaticText = wx.StaticText(
            containing_panel, style=wx.TRANSPARENT_WINDOW, label="SCORE"
        )
        row_grid.Add(control_label_score, pos=(1, 3), flag=wx.ALIGN_LEFT, border=5)
        self.__text_controls[data_field + "_SCORE"] = control_label_score

        # Connect grid sizer to panel.
        containing_panel.SetSizerAndFit(row_grid)

        self.__control_row += 1

    def __add_decision_radiobuttons(self) -> None:
        choices: list[str] = list(MatchDecision)

        self.__radio_box = wx.RadioBox(
            self.__my_panel,
            label="Classify the possible match",
            choices=choices[:3],
            majorDimension=1,
            style=wx.RA_SPECIFY_COLS,
        )
        self.Bind(wx.EVT_RADIOBOX, self.__on_box_select, self.__radio_box)

        # Not until we load data.
        self.__radio_box.Disable()

        # Leave extra row.
        self.__control_row += 1
        self.__my_grid.Add(
            self.__radio_box, pos=(self.__control_row, 0), flag=wx.ALIGN_LEFT, border=5
        )
        self.__control_row += 1

    def __add_header_row(self) -> None:
        """Create header for comparison block"""

        [containing_panel, row_grid] = self.__build_row(data_field="header")
        #
        #   The element name ("ADDR1")
        #
        control_label: wx.StaticText = wx.StaticText(containing_panel, label="Element")
        row_grid.Add(
            control_label,
            pos=(1, 0),
            flag=wx.ALIGN_LEFT,
            border=5,
        )
        #
        #   The AOU value ("ADDR1_AOU")
        #
        control_label_aou: wx.StaticText = wx.StaticText(containing_panel, label="AoU")
        row_grid.Add(control_label_aou, pos=(1, 1), flag=wx.ALIGN_LEFT, border=5)
        #
        #   The OMOP value ("ADDR1_OMOP")
        #
        control_label_omop: wx.StaticText = wx.StaticText(
            containing_panel, label="OMOP"
        )
        row_grid.Add(
            control_label_omop,
            pos=(1, 2),
            flag=wx.ALIGN_LEFT,
            border=5,
        )
        #
        #   The score ("ADDR1 SCORE")
        #
        control_label_score: wx.StaticText = wx.StaticText(
            containing_panel, label="Score"
        )
        row_grid.Add(
            control_label_score,
            pos=(1, 3),
            flag=wx.ALIGN_LEFT,
            border=5,
        )
        self.__my_grid.Add(
            wx.StaticLine(self.__my_panel, size=wx.Size(600, 2)),
            pos=(self.__control_row, 0),
            span=(1, 4),
            flag=wx.ALIGN_CENTER_HORIZONTAL,
            border=0,
        )

        # Connect grid sizer to panel.
        containing_panel.SetSizerAndFit(row_grid)

        self.__control_row += 1

    def __add_load_button(self) -> None:
        load_button: wx.Button = wx.Button(
            self.__my_panel,
            id=wx.ID_ANY,
            label="LOAD",
            size=wx.Size(110, 40),
            style=wx.BORDER_SUNKEN,
        )
        load_button.SetBackgroundColour(wx.Colour(255, 255, 255))
        load_button.Enable()
        self.__my_grid.Add(
            load_button,
            pos=(self.__control_row, 0),
            span=(1, 4),
            flag=wx.ALIGN_CENTER_HORIZONTAL,
            border=5,
        )
        load_button.Bind(wx.EVT_BUTTON, self.__on_load_file)
        self.__control_row += 1

    def __add_navigation_buttons(self) -> None:
        """Builds left/right buttons"""
        #
        #   LEFT BUTTON
        #
        img: wx.Image = wx.Image(
            os.path.join(self.__image_directory, "left_arrow.png"), wx.BITMAP_TYPE_PNG
        )

        if not img.IsOk():
            print("Failed to load image")

        self.__left_button: wx.BitmapButton = wx.BitmapButton(
            self.__my_panel,
            bitmap=wx.BitmapBundle.FromBitmap(wx.Bitmap(img)),
            id=wx.ID_ANY,
            size=wx.Size(50, 50),
            style=wx.BORDER_SUNKEN,
        )
        self.__left_button.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.__left_button.Disable()
        self.__my_grid.Add(
            self.__left_button, pos=(self.__control_row, 1), flag=wx.ALL, border=5
        )
        self.__left_button.Bind(wx.EVT_BUTTON, self.__on_go_left)
        #
        #   RIGHT BUTTON
        #
        img = wx.Image(
            os.path.join(self.__image_directory, "right_arrow.png"), wx.BITMAP_TYPE_PNG
        )
        self.__right_button: wx.BitmapButton = wx.BitmapButton(
            self.__my_panel,
            bitmap=wx.BitmapBundle.FromBitmap(wx.Bitmap(img)),
            id=wx.ID_ANY,
            size=wx.Size(50, 50),
            style=wx.BORDER_SUNKEN,
        )
        self.__right_button.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.__right_button.Disable()
        self.__my_grid.Add(
            self.__right_button, pos=(self.__control_row, 2), flag=wx.ALL, border=5
        )
        self.__right_button.Bind(wx.EVT_BUTTON, self.__on_go_right)
        self.__control_row += 1

    def __add_progress_info(self) -> None:
        """Builds progress bar & label"""

        # PROGRESS TEXT
        self.__progress_text = wx.StaticText(self.__my_panel, id=wx.ID_ANY, label="-")
        self.__my_grid.Add(
            self.__progress_text,
            pos=(self.__control_row, 0),
            span=(1, 4),
            flag=wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL | wx.ALL,
            border=5,
        )
        self.__control_row += 1

        # PROGRESS BAR
        self.__progress_gauge = wx.Gauge(
            self.__my_panel, range=100, size=wx.Size(300, 15)
        )
        self.__my_grid.Add(
            self.__progress_gauge,
            pos=(self.__control_row, 0),
            span=(1, 4),
            flag=wx.EXPAND | wx.ALL,
            border=5,
        )
        self.__control_row += 1

    def __add_save_and_cancel_buttons(self) -> None:
        """Build save/cancel buttons"""
        #
        #   WRITE BUTTON
        #
        self.__save_button: wx.Button = wx.Button(
            self.__my_panel,
            id=wx.ID_ANY,
            label="SAVE",
            size=wx.Size(110, 40),
            style=wx.BORDER_SUNKEN,
        )
        self.__save_button.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.__save_button.Disable()
        self.__my_grid.Add(
            self.__save_button, pos=(self.__control_row, 1), flag=wx.ALL, border=5
        )
        self.__save_button.Bind(wx.EVT_BUTTON, self.__on_save)
        #
        #   CANCEL BUTTON
        #
        cancel_button: wx.Button = wx.Button(
            self.__my_panel,
            id=wx.ID_ANY,
            label="CANCEL",
            size=wx.Size(110, 40),
            style=wx.BORDER_SUNKEN,
        )
        cancel_button.SetBackgroundColour(wx.Colour(255, 255, 255))
        cancel_button.Enable()
        self.__my_grid.Add(
            cancel_button, pos=(self.__control_row, 2), flag=wx.ALL, border=5
        )
        cancel_button.Bind(wx.EVT_BUTTON, self.__on_cancel)
        self.__control_row += 1

    def __add_single_info(self, data_field: str) -> None:
        """
            Create info labels like "MRN 12345"

        Parameters
        ----------
        data_field:     What the dataframe calls this data element

        Returns
        -------
        none
        """
        #
        #   The element name ("MRN")
        #
        control_label: wx.StaticText = wx.StaticText(
            self.__my_panel, id=wx.ID_ANY, label=data_field
        )
        self.__my_grid.Add(
            control_label, pos=(self.__control_row, 0), flag=wx.ALIGN_LEFT, border=5
        )
        #
        #   The value ("MRN")
        #
        control_label_value: wx.StaticText = wx.StaticText(
            self.__my_panel, id=wx.ID_ANY, label="-"
        )
        self.__my_grid.Add(
            control_label_value,
            pos=(self.__control_row, 1),
            flag=wx.EXPAND | wx.ALIGN_LEFT,
            border=5,
        )
        self.__text_controls[data_field] = control_label_value
        self.__control_row += 1

    def __add_title(self, label: str) -> None:
        """
        Adds a title at the top of the panel.

        Parameters
        ----------
        label: str

        """

        # Title
        title_font: wx.Font = wx.Font(
            16,
            family=wx.FONTFAMILY_ROMAN,
            style=wx.FONTSTYLE_NORMAL,
            weight=wx.FONTWEIGHT_BOLD,
        )
        title_text: wx.StaticText = wx.StaticText(
            self.__my_panel,
            id=wx.ID_ANY,
            label=label,
        )
        title_text.SetFont(title_font)
        self.__my_grid.Add(
            title_text,
            pos=(self.__control_row, 0),
            span=(1, 4),
            flag=wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL | wx.ALL,
            border=5,
        )
        self.__my_grid.AddGrowableCol(idx=1, proportion=1)
        self.__control_row += 1

    def __build_row(self, data_field: str) -> tuple[wx.Panel, wx.GridBagSizer]:
        """
            Build a row to hold other controls.
        Parameters
        ----------
        data_field

        Returns tuple of
        -------
        containing_panel: wx.Panel
        row_grid: wx.GridBagSizer
        """
        row_grid: wx.GridBagSizer = wx.GridBagSizer(hgap=5, vgap=5)
        row_grid.Add(
            width=200,
            height=5,
            pos=(0, 0),
            flag=wx.ALIGN_CENTER_HORIZONTAL,
            border=5,
        )
        row_grid.Add(
            width=200,
            height=5,
            pos=(0, 1),
            flag=wx.ALIGN_CENTER_HORIZONTAL,
            border=5,
        )
        row_grid.Add(
            width=200,
            height=5,
            pos=(0, 2),
            flag=wx.ALIGN_CENTER_HORIZONTAL,
            border=5,
        )
        row_grid.Add(
            width=200,
            height=5,
            pos=(0, 3),
            flag=wx.ALIGN_CENTER_HORIZONTAL,
            border=5,
        )

        # Name the row's panel with the root name (so we can find it).
        containing_panel: wx.Panel = wx.Panel(
            self.__my_panel, size=wx.Size(400, 25), name=data_field
        )
        containing_panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.__my_grid.Add(
            containing_panel,
            pos=(self.__control_row, 0),
            flag=wx.ALIGN_LEFT,
            border=5,
            span=(1, 4),
        )

        self.__control_row += 1
        return containing_panel, row_grid

    def __enable_upon_load(self) -> None:
        """Once data loaded, allows us to enable navigation, decision buttons, etc."""
        self.__right_button.Enable()
        self.__save_button.Enable()
        self.__radio_box.Enable()

    def __go_to_next_record(self) -> None:
        """Move to the next record."""
        if self.__row < len(self.df):
            self.__log.info("Go to next record.")
            self.__row += 1

            if self.__row == len(self.df) - 1:
                self.__right_button.Disable()
            else:
                self.__right_button.Enable()

            self.__left_button.Enable()
            self.__populate_data()
            self.__set_radiobuttons()
            self.__update_progress()

    def __load_file(self, file_path: str) -> None:
        """
            - Reads file into DataFrame
            - Populates the controls from dataframe first row.

        Parameters
        ----------
        file_path: str
        """
        if file_path:
            # Save for next time.
            self.__config["Settings"]["manual_decision_file_path"] = file_path
            write_config(self.__config, self.__log)

            try:
                # Read match file.
                self.df = Wobbler.read_wobbler_file(
                    match_file=file_path, log=self.__log
                )

                if self.df.empty:
                    self.__log.error(f"Unable to read file {file_path}.")
                    return

                self.__row = 0
                self.__populate_data()
                self.__set_radiobuttons()
                self.__update_progress()
                self.__enable_upon_load()

            except FileNotFoundError as e:
                self.__log.exception(f"File {file_path} not found.")
                raise

    @staticmethod
    def __map_score_to_color(score: str) -> wx.Colour:
        """
        Convert score (0 to 100) to color (yellow to white).

        Parameters
        ----------
        score: str

        Returns
        -------
        color: wx.Colour
        """
        red: int = 255
        green: int = 255
        blue: int

        # Score of 0 maps to blue = 0 ==> color is all yellow.
        # Score of 100 maps to blue = 255 ==> color is white.
        try:
            blue = int(2.55 * int(score))
        except ValueError:
            blue = 0  # Fallback value

        return wx.Colour(red, green, blue)

    def __on_box_select(self, event: wx.CommandEvent) -> None:
        """
        Event handler for the radio box select.

        Parameters
        ----------
        event

        """
        match_decision: MatchDecision = MatchDecision.NONE

        match event.GetString():
            case "MATCH":
                match_decision = MatchDecision.MATCH

            case "NO_MATCH":
                match_decision = MatchDecision.NO_MATCH

            case "UNSURE":
                match_decision = MatchDecision.UNSURE

        self.df.at[self.df.index[self.__row], "MATCH"] = match_decision
        self.__go_to_next_record()

    def __on_cancel(self, event: wx.CommandEvent) -> None:
        """
        Event handler for cancel button.

        Parameters
        ----------
        event

        """
        self.__log.info("Cancelled.")
        event.Skip()
        self.Destroy()

    def __on_close(self, event: wx.CloseEvent) -> None:
        """
        Ensure external thread is stopped before GUI closes.
        """
        self.__log.info("GUI closing.")
        event.Skip()
        self.Destroy()

    def __on_go_left(self, event: wx.CommandEvent) -> None:
        """
        Event handler for go back one record.

        Parameters
        ----------
        event

        """

        self.__log.info("Go back one record.")
        self.__row -= 1

        if self.__row == 0:
            # Can't go backwards.
            self.__left_button.Disable()
        else:
            self.__left_button.Enable()

        self.__right_button.Enable()
        self.__populate_data()
        self.__set_radiobuttons()
        self.__update_progress()

    def __on_go_right(self, event: wx.CommandEvent) -> None:
        """
        Event handler for go forward one record.

        Parameters
        ----------
        event

        """
        decision: MatchDecision = self.__read_classification()
        self.df.at[self.df.index[self.__row], "MATCH"] = decision
        self.__go_to_next_record()

    def __on_load_file(self, event: wx.CommandEvent) -> None:
        """
        Event handler for when user presses LOAD button:
            - Asks for file
            - Hands off to __load_file()

        Parameters
        ----------
        event

        Returns
        -------
        None
        """
        initial_dir: Path = Path("/")

        if self.__config.has_option("Settings", "manual_decision_file_path"):
            initial_dir = Path(
                self.__config["Settings"]["manual_decision_file_path"]
            ).parent

        # Open the file selection dialog.
        file_path: str = filedialog.askopenfilename(
            title="Select Match File",
            initialdir=initial_dir,  # Optional: Set an initial directory
        )

        self.__load_file(file_path)

    def __on_match(self, event: wx.CommandEvent) -> None:
        """
            Event handler for when user presses MATCH button:

        Parameters
        ----------
        event

        Returns
        -------
        None
        """
        self.df.at[self.df.index[self.__row], "MATCH"] = MatchDecision.MATCH.value
        self.__go_to_next_record()

    def __on_meh(self, event: wx.CommandEvent) -> None:
        """
            Event handler for when user presses UNSURE button:

        Parameters
        ----------
        event

        Returns
        -------
        None
        """
        self.df.at[self.df.index[self.__row], "MATCH"] = MatchDecision.UNSURE
        self.__go_to_next_record()

    def __on_no_match(self, event: wx.CommandEvent) -> None:
        """
            Event handler for when user presses NO MATCH button:

        Parameters
        ----------
        event

        Returns
        -------
        None
        """
        self.df.at[self.df.index[self.__row], "MATCH"] = MatchDecision.NO_MATCH
        self.__go_to_next_record()

    def __on_save(self, event: wx.CommandEvent) -> None:
        """
        Event handler for when user presses SAVE button:

        Parameters
        ----------
        event

        """
        # Record the final potential match.
        decision: MatchDecision = self.__read_classification()
        self.df.at[self.df.index[self.__row], "MATCH"] = decision

        # Synthesize new filename as <old file name>_reviewed.txt
        full_file_path: Path = Path(
            self.__config["Settings"]["manual_decision_file_path"]
        )
        just_the_filename: str = full_file_path.stem
        ext: str = full_file_path.suffix
        timestamp_filesafe: str = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_file: str = str(
            full_file_path.with_name(
                f"{just_the_filename}_reviewed_{timestamp_filesafe}{ext}"
            )
        )

        if Wobbler.write_wobbler_file(match_file=new_file, df=self.df, log=self.__log):
            wx.MessageBox(
                f"Wrote {len(self.df)} records to {new_file}.",
                "Info",
                wx.OK | wx.ICON_INFORMATION,
            )

    def __populate_data(self) -> None:
        """
        Pushes the contents of the DataFrame into the controls.
        """
        data_fields: list[str] = list(self.__text_controls)

        for data_field in data_fields:
            data_value: str = self.df[data_field].iloc[self.__row]
            control_label: wx.StaticText = self.__text_controls[data_field]

            if isinstance(data_value, str):
                control_label.SetLabel(data_value)
            else:
                control_label.SetLabel("")

            # Determine background color based on the "SCORE" field.
            if "SCORE" in data_field and not "TOTAL_SCORE" in data_field:
                self.__shade_row_based_on_score(control_label)

    def __read_classification(self) -> MatchDecision:
        """
            Read radio buttons & return match decision.

        Returns
        -------
        decision: MatchDecision
        """
        decision: MatchDecision = MatchDecision.UNSURE
        selection: str = self.__radio_box.GetStringSelection()

        if selection == MatchDecision.MATCH.value:
            decision: MatchDecision = MatchDecision.MATCH
        elif selection == MatchDecision.UNSURE.value:
            decision: MatchDecision = MatchDecision.UNSURE
        elif selection == MatchDecision.NO_MATCH.value:
            decision: MatchDecision = MatchDecision.NO_MATCH

        return decision

    def __set_radiobuttons(self) -> None:
        """
        Pre-click the radiobuttons based on recorded classification.
        """
        decision: MatchDecision = self.df.at[self.df.index[self.__row], "MATCH"]

        match decision:
            case MatchDecision.MATCH:
                self.__radio_box.SetStringSelection("MATCH")
            case MatchDecision.UNSURE:
                self.__radio_box.SetStringSelection("UNSURE")
            case MatchDecision.NO_MATCH:
                self.__radio_box.SetStringSelection("NO_MATCH")

    def __shade_row_based_on_score(self, score_label: wx.StaticText) -> None:
        """
            Set BackgroundColour attribute of the panel linked to this score field.

        Parameters
        ----------
        score_label: wx.StaticText
        """
        score_value: str = score_label.GetLabel()
        background_color = self.__map_score_to_color(score_value)

        # Find parent panel.
        panel_this_row: wx.Panel = score_label.GetParent()

        # Shade the row.
        panel_this_row.SetBackgroundColour(background_color)
        self.Refresh()
        self.Update()

    def __update_progress(self) -> None:
        """
        Update progress bar & text.
        """
        self.__log.debug(f"Received low-level call to update progress.")
        self.__progress_text.SetLabel(
            f"Processing {self.__row} of {len(self.df)} records."
        )
        pct: int = int(100.0 * self.__row / len(self.df))
        self.__progress_gauge.SetValue(pct)

    def __write_config(self) -> None:
        # 1. Initialize the parser
        config = ConfigParser()

        # 2. Add a section and the file path
        config.add_section("Settings")
        config.set(
            "Settings", "manual_decision_file_directory", "/path/to/your/file.txt"
        )

        # 3. Save to a file named 'config.ini'
        with open("config.ini", "w") as configfile:
            config.write(configfile)
