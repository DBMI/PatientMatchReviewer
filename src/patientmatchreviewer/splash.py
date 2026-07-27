"""
Contains MySplashScreen class.
"""

from importlib import resources
import io
import wx
import wx.adv


# pylint: disable=too-few-public-methods
class MySplashScreen(wx.adv.SplashScreen):
    """
    Creates a splash screen at startup.
    """

    def __init__(self, filename: str):
        """
        Instantiates the splash screen.

        Parameters
        ----------
        filename: str
        """
        # Load file bytes from package resources
        data = resources.files("patientmatchreviewer").joinpath(filename).read_bytes()

        # Read into a stream and convert to bitmap.
        stream = io.BytesIO(data)
        image = wx.Image(stream)

        wx.adv.SplashScreen.__init__(
            self,
            wx.Bitmap(image),
            wx.adv.SPLASH_CENTRE_ON_SCREEN | wx.adv.SPLASH_TIMEOUT,
            2500,
            None,
            -1,
        )


if __name__ == "__main__":
    app: wx.App = wx.App()
    splash_frame: MySplashScreen = MySplashScreen(
        r"pictures/UCSD_school_of_medicine.png"
    )
    splash_frame.Show()
    app.MainLoop()
