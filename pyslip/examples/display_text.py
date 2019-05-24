"""
A wxPython custom widget used by pySlip.

Used to display text.  The layout and components:

    +-----------------------------------------+
    |  <title>                                |
    |                                         |
    |                  +----------------+     |
    |       <label>    | <text>         |     |
    |                  +----------------+     |
    |                                         |
    +-----------------------------------------+

The constructor:

    dt = DisplayText(parent, title='', label='', textwidth=None, tooltip=None)

    where title      is the text to display at the top of the widget
          label      is the text to the left of the displayed <text>
          textwidth  is the width (in pixels) of the <text> field
          tooltip    is the text of a tooltip for the widget

Methods:

    dt.set_text("some text")
    dt.clear()

"""

import wx
from appstaticbox import AppStaticBox

class DisplayText(wx.Frame):

    # some subwidget sizes
    LabelWidth = 30


    def __init__(self, title, label, tooltip=None, text_width=None):
        super().__init__()

        # handle any text width request
        size = (text_width, -1)
        if text_width is None:
            size = (DisplayText.LabelWidth, -1)

        # create objects
        self.txt = wx.StaticText(self, wx.ID_ANY, label)
        self.map_level = ROTextCtrl(self, '', size=size, tooltip=tooltip)

        # lay out the controls
        sb = AppStaticBox(self, title)
        box = wx.StaticBoxSizer(sb, orient=wx.HORIZONTAL)
        box.Add(self.txt, border=PackBorder, flag=(wx.ALIGN_CENTER_VERTICAL
                                              |wx.ALIGN_RIGHT|wx.LEFT))
        box.Add(self.map_level, proportion=0, border=PackBorder,
                flag=wx.LEFT|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)

    def set_text(self, text):
        """Set the text of the display field.

        text the text to show
        """

        self.text.SetValue(text)
