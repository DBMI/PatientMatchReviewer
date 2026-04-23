"""
Contains MySplashScreen class.
"""
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
        bmp: wx.Bitmap = wx.Bitmap(filename, wx.BITMAP_TYPE_PNG)
        wx.adv.SplashScreen.__init__(
            self,
            bmp,
            wx.adv.SPLASH_CENTRE_ON_SCREEN | wx.adv.SPLASH_TIMEOUT,
            2500,
            None,
            -1,
        )


if __name__ == "__main__":
    app: wx.App = wx.App()
    splash_frame: MySplashScreen = MySplashScreen(r"UCSD_school_of_medicine.png")
    splash_frame.Show()
    app.MainLoop()
