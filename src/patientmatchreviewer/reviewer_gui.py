"""
Module: Contains class ReviewerGui, which creates the GUI
        users can use to review patient matching data.
"""

from configparser import ConfigParser
import logging
import os
import pandas
import wx
import wx.adv
from pathlib import Path
from tkinter import filedialog

from src.patientmatchreviewer.common import get_config, resource_path, write_config
from src.patientmatchreviewer.wobbler import MatchDecision, Wobbler


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

    def __init__(self, log: logging.Logger) -> None:
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
            weight=wx.FONTWEIGHT_NORMAL
        )

        # Create grid.
        self.__my_grid: wx.GridBagSizer = wx.GridBagSizer(hgap=5, vgap=5)

        # Add title
        self.__control_row: int = 0
        self.__add_title(label="Review possible patient matches")

        # Dictionaries of controls linking labels with their DataFrame fields.
        self.__labels_and_fields: dict = {}

        # Where to find image files.
        self.__image_directory: str = resource_path(r'..\..\pictures')
        #
        #   LOAD BUTTON
        #
        self.df: pandas.DataFrame
        self.__add_load_button()
        # Leave empty row
        self.__control_row += 1

        # Keep track of row in dataframe.
        self.__row: int = 0
        #
        #   HEADER INFORMATION
        #
        self.__add_single_info(data_field="PMI_ID")
        self.__add_single_info(data_field="OMOP_ID")
        self.__add_single_info(data_field="MRN")
        #
        #   RECORD COMPARISON
        #
        self.__add_header_row()
        self.__add_commparison_row(data_field="GIVEN_NAME")
        self.__add_commparison_row(data_field="FAMILY_NAME")
        self.__add_commparison_row(data_field="DOB")
        self.__add_commparison_row(data_field="ADDR1")
        self.__add_commparison_row(data_field="PHONE1")
        self.__add_commparison_row(data_field="PHONE2")
        self.__add_single_info(data_field="TOTAL_SCORE")
        #
        #   DECISION BUTTONS
        #
        self.__match_button: wx.Button
        self.__no_match_button: wx.Button
        self.__meh_button: wx.Button
        self.__add_decision_buttons()
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
        self.ShowModal()

    def __add_commparison_row(self, data_field: str) -> None:
        """
            Create comparison row like "FAMILY NAME:    Smith   Smyth   79"

        Parameters
        ----------
        data_field:     Root name for what the dataframe calls these three data elements
                        For example, if "dob", the dataframe should contain columns
                                "DOB AOU"
                                "DOB OMOP"
                                "DOB SCORE"
        Returns
        -------
        none
        """
        #
        #   The element name ("ADDR1")
        #
        control_label: wx.StaticText = wx.StaticText(
            self.__my_panel, id=wx.ID_ANY, label= data_field
        )
        self.__my_grid.Add(control_label, pos=(self.__control_row, 0), flag=wx.ALIGN_LEFT, border=5)
        #
        #   The AOU value ("ADDR1_AOU")
        #
        control_label_aou: wx.StaticText = wx.StaticText(
            self.__my_panel, id=wx.ID_ANY, label= "AOU"
        )
        self.__my_grid.Add(control_label_aou, pos=(self.__control_row, 1), flag=wx.ALIGN_LEFT, border=5)

        # Register this control against this data field.
        self.__labels_and_fields[data_field + "_AOU"] = control_label_aou
        #
        #   The OMOP value ("ADDR1_OMOP")
        #
        control_label_omop: wx.StaticText = wx.StaticText(
            self.__my_panel, id=wx.ID_ANY, label="OMOP"
        )
        self.__my_grid.Add(control_label_omop, pos=(self.__control_row, 2), flag=wx.ALIGN_LEFT, border=5)

        # Register this control against this data field.
        self.__labels_and_fields[data_field + "_OMOP"] = control_label_omop
        #
        #   The score ("ADDR1 SCORE")
        #
        control_label_score: wx.StaticText = wx.StaticText(
            self.__my_panel, id=wx.ID_ANY, label="SCORE"
        )
        self.__my_grid.Add(control_label_score, pos=(self.__control_row, 3), flag=wx.ALIGN_RIGHT, border=5)

        # Register this control against this data field.
        self.__labels_and_fields[data_field + "_SCORE"] = control_label_score
        self.__control_row += 1

    def __add_decision_buttons(self) -> None:
        #
        #   MATCH BUTTON
        #
        self.__match_button: wx.Button = wx.Button(
            self.__my_panel,
            id=wx.ID_ANY,
            label="MATCH",
            size=wx.Size(110, 40),
            style=wx.BORDER_SUNKEN,
        )
        #self.__match_button.SetFont(small_font)
        self.__match_button.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.__match_button.Disable()
        self.__my_grid.Add(self.__match_button, pos=(self.__control_row, 0), flag=wx.ALL, border=2)
        self.__match_button.Bind(wx.EVT_BUTTON, self.__on_match)
        self.__control_row += 1
        #
        #   NO MATCH BUTTON
        #
        self.__no_match_button: wx.Button = wx.Button(
            self.__my_panel,
            id=wx.ID_ANY,
            label="NO MATCH",
            size=wx.Size(110, 40),
            style=wx.BORDER_SUNKEN,
        )
        #self.__no_match_button.SetFont(small_font)
        self.__no_match_button.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.__no_match_button.Disable()
        self.__my_grid.Add(self.__no_match_button, pos=(self.__control_row, 0), flag=wx.ALL, border=2)
        self.__no_match_button.Bind(wx.EVT_BUTTON, self.__on_no_match)
        self.__control_row +=1
        #
        #   MEH BUTTON
        #
        self.__meh_button: wx.Button = wx.Button(
            self.__my_panel,
            id=wx.ID_ANY,
            label="UNSURE",
            size=wx.Size(110, 40),
            style=wx.BORDER_SUNKEN,
        )
        #self.__meh_button.SetFont(small_font)
        self.__meh_button.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.__meh_button.Disable()
        self.__my_grid.Add(self.__meh_button, pos=(self.__control_row, 0), flag=wx.ALL, border=2)
        self.__meh_button.Bind(wx.EVT_BUTTON, self.__on_meh)
        self.__control_row += 1

    def __add_header_row(self) -> None:
        """ Create header for comparison block """

        # Force columns to be at least a certain size.
        self.__my_grid.Add(width=120, height=10, pos=(self.__control_row, 1),flag=wx.ALIGN_CENTER_HORIZONTAL, border=5)
        self.__my_grid.Add(width=120, height=10, pos=(self.__control_row, 2),flag=wx.ALIGN_CENTER_HORIZONTAL, border=5)
        self.__control_row += 1
        #
        #   The element name ("ADDR1")
        #
        control_label: wx.StaticText = wx.StaticText(
            self.__my_panel, id=wx.ID_ANY, label= "Element"
        )
        self.__my_grid.Add(control_label, pos=(self.__control_row, 0), flag=wx.ALIGN_LEFT, border=5)
        #
        #   The AOU value ("ADDR1_AOU")
        #
        control_label_aou: wx.StaticText = wx.StaticText(
            self.__my_panel, id=wx.ID_ANY, label= "AoU"
        )
        self.__my_grid.Add(control_label_aou, pos=(self.__control_row, 1), flag=wx.ALIGN_LEFT, border=5)
        #
        #   The OMOP value ("ADDR1_OMOP")
        #
        control_label_omop: wx.StaticText = wx.StaticText(
            self.__my_panel, id=wx.ID_ANY, label="OMOP"
        )
        self.__my_grid.Add(control_label_omop, pos=(self.__control_row, 2), flag=wx.ALIGN_LEFT, border=5)
        #
        #   The score ("ADDR1 SCORE")
        #
        control_label_score: wx.StaticText = wx.StaticText(
            self.__my_panel, id=wx.ID_ANY, label="Score"
        )
        self.__my_grid.Add(control_label_score, pos=(self.__control_row, 3), flag=wx.ALIGN_RIGHT, border=5)
        self.__control_row += 1
        self.__my_grid.Add(wx.StaticLine(self.__my_panel,size=wx.Size(400, 2)),
                           pos=(self.__control_row, 0),
                           span=(1,4),
                           flag=wx.ALIGN_CENTER_HORIZONTAL,
                           border=0)
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
        self.__my_grid.Add(load_button,
                           pos=(self.__control_row, 0),
                           span=(1,4),
                           flag=wx.ALIGN_CENTER_HORIZONTAL,
                           border=5)
        load_button.Bind(wx.EVT_BUTTON, self.__on_load_file)
        self.__control_row += 1

    def __add_navigation_buttons(self) -> None:
        """ Builds left/right buttons """
        #
        #   LEFT BUTTON
        #
        img: wx.Image = wx.Image(os.path.join(self.__image_directory, 'left_arrow.png'), wx.BITMAP_TYPE_PNG)

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
        self.__my_grid.Add(self.__left_button, pos=(self.__control_row, 1), flag=wx.ALL, border=5)
        self.__left_button.Bind(wx.EVT_BUTTON, self.__on_go_left)
        #
        #   RIGHT BUTTON
        #
        img = wx.Image(os.path.join(self.__image_directory, 'right_arrow.png'), wx.BITMAP_TYPE_PNG)
        self.__right_button: wx.BitmapButton = wx.BitmapButton(
            self.__my_panel,
            bitmap=wx.BitmapBundle.FromBitmap(wx.Bitmap(img)),
            id=wx.ID_ANY,
            size=wx.Size(50, 50),
            style=wx.BORDER_SUNKEN,
        )
        self.__right_button.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.__right_button.Disable()
        self.__my_grid.Add(self.__right_button, pos=(self.__control_row, 2), flag=wx.ALL, border=5)
        self.__right_button.Bind(wx.EVT_BUTTON, self.__on_go_right)
        self.__control_row += 1

    def __add_progress_info(self) -> None:
        """ Builds progress bar & label """

        # PROGRESS TEXT
        self.__progress_text = wx.StaticText(self.__my_panel, id=wx.ID_ANY, label="-")
        self.__my_grid.Add(
            self.__progress_text,
            pos=(self.__control_row, 0),
            span=(1, 4),
            flag=wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL | wx.ALL,
            border=5,
        )
        self.__control_row +=1

        # PROGRESS BAR
        self.__progress_gauge = wx.Gauge(self.__my_panel, range=100, size=wx.Size(300, 15))
        self.__my_grid.Add(
            self.__progress_gauge,
            pos=(self.__control_row, 0),
            span=(1,4),
            flag=wx.EXPAND | wx.ALL,
            border=5,
        )
        self.__control_row += 1

    def __add_save_and_cancel_buttons(self) -> None:
        """ Build save/cancel buttons """
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
        self.__my_grid.Add(self.__save_button, pos=(self.__control_row, 1), flag=wx.ALL, border=5)
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
        self.__my_grid.Add(cancel_button, pos=(self.__control_row, 2), flag=wx.ALL, border=5)
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
            self.__my_panel, id=wx.ID_ANY, label= data_field
        )
        self.__my_grid.Add(control_label, pos=(self.__control_row, 0), flag=wx.ALIGN_LEFT, border=5)
        #
        #   The value ("MRN")
        #
        control_label_value: wx.StaticText = wx.StaticText(
            self.__my_panel, id=wx.ID_ANY, label= "-"
        )
        self.__my_grid.Add(control_label_value, pos=(self.__control_row, 1), flag=wx.EXPAND | wx.ALIGN_LEFT, border=5)

        # Register this control against this data field.
        self.__labels_and_fields[data_field] = control_label_value
        self.__control_row += 1

    def __add_title(self, label: str) -> None:
        """
        Adds a title at the top of the panel.

        Parameters
        ----------
        label: str

        Returns
        -------
        None
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
            flag= wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL | wx.ALL,
            border=5,
        )
        self.__my_grid.AddGrowableCol(idx=1, proportion=1)
        self.__control_row += 1

    def __enable_upon_load(self) -> None:
        """ Once data loaded, allows us to enable navigation, decision buttons, etc."""
        self.__right_button.Enable()
        self.__save_button.Enable()
        self.__match_button.Enable()
        self.__no_match_button.Enable()
        self.__meh_button.Enable()

    def __go_to_next_record(self) -> None:
        """ Move to the next record."""

        if self.__row < len(self.df):
            self.__log.info("Go to next record.")
            self.__row += 1

            if self.__row == len(self.df) - 1:
                self.__right_button.Disable()
            else:
                self.__right_button.Enable()

            self.__left_button.Enable()
            self.__populate_data()
            self.__update_progress()

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
        self.__update_progress()

    def __on_go_right(self, event: wx.CommandEvent) -> None:
        """
        Event handler for go forward one record.

        Parameters
        ----------
        event

        """
        self.__go_to_next_record()

    def __on_load_file(self, event: wx.CommandEvent) -> None:
        """
        Event handler for when user presses LOAD button:
            - Asks for file
            - Reads file into DataFrame
            - Populates the controls from dataframe first row.

        Parameters
        ----------
        event

        Returns
        -------
        None
        """
        initial_dir: Path = Path("/")

        if self.__config.has_option('Settings', 'manual_decision_file_path'):
            initial_dir = Path(self.__config['Settings']['manual_decision_file_path']).parent

        # Open the file selection dialog.
        file_path: str = filedialog.askopenfilename(
            title="Select Match File",
            initialdir=initial_dir,  # Optional: Set an initial directory
        )

        if file_path:
            # Save for next time.
            self.__config["Settings"]["manual_decision_file_path"] = file_path
            write_config(self.__config, self.__log)

            try:
                # Read match file.
                self.df = Wobbler.read_wobbler_file(match_file=file_path, log=self.__log)

                if self.df.empty:
                    self.__log.error(f"Unable to read file {file_path}.")
                    return

                self.__row = 0
                self.__populate_data()
                self.__update_progress()
                self.__enable_upon_load()

            except FileNotFoundError as e:
                self.__log.exception(f"File {file_path} not found.")
                raise

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
        # Synthesize new filename as <old file name>_reviewed.txt
        full_file_path: Path = Path(self.__config['Settings']['manual_decision_file_path'])
        just_the_filename: str = full_file_path.stem
        ext: str = full_file_path.suffix
        new_file: str = str(full_file_path.with_name(f"{just_the_filename}_reviewed{ext}"))

        Wobbler.write_wobbler_file(match_file=new_file, df=self.df, log=self.__log)

    def __populate_data(self) -> None:
        """
            Pushes the contents of the DataFrame into the controls.
        """
        data_fields: list = list(self.__labels_and_fields.keys())

        for data_field in data_fields:
            data_value: str = self.df[data_field].iloc[self.__row]
            control_label: wx.StaticText = self.__labels_and_fields[data_field]

            if control_label:
                control_label.SetLabel(data_value)

    def __update_progress(self) -> None:
        """
        Update progress bar & text.
        """
        self.__log.debug(f"Received low-level call to update progress.")
        self.__progress_text.SetLabel(f"Processing {self.__row} of {len(self.df)} records.")
        pct: int = int(100.0 * self.__row / len(self.df))
        self.__progress_gauge.SetValue(pct)

    def __write_config(self) -> None:
        # 1. Initialize the parser
        config = configparser.ConfigParser()

        # 2. Add a section and the file path
        config.add_section('Settings')
        config.set('Settings', 'manual_decision_file_directory', '/path/to/your/file.txt')

        # 3. Save to a file named 'config.ini'
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
