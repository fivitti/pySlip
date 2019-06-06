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
#from rotextctrl import ROTextCtrl

###############################################################################
# Override the wx.TextCtrl class to add read-only style and background colour
###############################################################################

# background colour for the 'read-only' text field
ControlReadonlyColour = '#ffffcc'

class ROTextCtrl(wx.TextCtrl):
    """Override the wx.TextCtrl widget to get read-only text control which
    has a distinctive background colour."""

    def __init__(self, parent, value, tooltip='', *args, **kwargs):
        wx.TextCtrl.__init__(self, parent, wx.ID_ANY, value=value,
                             style=wx.TE_READONLY, *args, **kwargs)
        self.SetBackgroundColour(ControlReadonlyColour)
#        self.SetToolTip(wx.ToolTip(tooltip))
        self.SetToolTip(tooltip)

###############################################################################
# Define the custom widget.
###############################################################################

class DisplayText(wx.Panel):

    # some subwidget sizes
    LabelWidth = 30


    def __init__(self, parent, title, label, tooltip=None, text_width=None):
        super().__init__(parent)

        print('DisplayText class: point 1', flush=True)

        # handle any text width request
        size = (text_width, -1)
        if text_width is None:
            size = (DisplayText.LabelWidth, -1)

        print('DisplayText class: point 2', flush=True)

        # create objects
        self.txt = wx.StaticText(self, wx.ID_ANY, label)
        print('DisplayText class: point 2.5', flush=True)
        self.map_level = ROTextCtrl(self, '', size=size, tooltip=tooltip)

        print('DisplayText class: point 3', flush=True)

        # lay out the controls
        sb = AppStaticBox(self, title)
        box = wx.StaticBoxSizer(sb, orient=wx.HORIZONTAL)
#        box.Add(self.map_level, proportion=0, border=PackBorder,
#                flag=wx.LEFT|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        box.Add(self.map_level, proportion=0,
                flag=wx.LEFT|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)

        print('DisplayText class: point 9', flush=True)

    def set_text(self, text):
        """Set the text of the display field.

        text the text to show
        """

        self.text.SetValue(text)
