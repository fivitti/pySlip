"""
Test the DisplayText custom widget used by pySlip.
"""

import wx
from display_text import DisplayText

######
# Various constants
######

DemoWidth = 600
DemoWidth = 400
DefaultAppSize = (DemoWidth, DemoWidth)

MinTileLevel = 0
InitViewLevel = 2
InitViewPosition = (158.0, -20.0)

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
        self.SetToolTip(wx.ToolTip(tooltip))

###############################################################################
# The test farme.
###############################################################################

class TestFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, size=DefaultAppSize,
                          title=('PySlip %s - map-relative image test' % '0.1'))
        self.SetMinSize(DefaultAppSize)
        self.panel = wx.Panel(self, wx.ID_ANY)
        self.panel.SetBackgroundColour(wx.WHITE)
        self.panel.ClearBackground()
        print('After setup, just before DisplayText()', flush=True)

        # create the text DisplayText widget
        DisplayText(self.panel, 'title', 'label')
        print('After DisplayText()')

        # build the GUI
        box = wx.BoxSizer(wx.HORIZONTAL)
        self.panel.SetSizer(box)
        self.dt = DisplayText(self, 'title', 'label')
        box.Add(self.dt, proportion=1, border=1, flag=wx.EXPAND)
        self.panel.SetSizerAndFit(box)
        self.panel.Layout()
        print('Just before Centre()')
        self.Centre()
        print('Just before Show()')
        self.Show(True)

################################################################################

if __name__ == '__main__':
    import sys
    import getopt
    import traceback

    # print some usage information
    def usage(msg=None):
        if msg:
            print(msg+'\n')
        print(__doc__)        # module docstring used

    # our own handler for uncaught exceptions
    def excepthook(type, value, tb):
        msg = '\n' + '=' * 80
        msg += '\nUncaught exception:\n'
        msg += ''.join(traceback.format_exception(type, value, tb))
        msg += '=' * 80 + '\n'
        print(msg)
        sys.exit(1)
    sys.excepthook = excepthook

    # decide which tiles to use, default is GMT
    argv = sys.argv[1:]

    try:
        (opts, args) = getopt.getopt(argv, 'ht:', ['help', 'tiles='])
    except getopt.error:
        usage()
        sys.exit(1)

    tile_source = 'GMT'
    for (opt, param) in opts:
        if opt in ['-h', '--help']:
            usage()
            sys.exit(0)
        elif opt in ('-t', '--tiles'):
            tile_source = param
    tile_source = tile_source.lower()

    # set up the appropriate tile source
    if tile_source == 'gmt':
        import pyslip.gmt_local as Tiles
    elif tile_source == 'osm':
        import pyslip.open_street_map as Tiles
    else:
        usage('Bad tile source: %s' % tile_source)
        sys.exit(3)

    print('Starting the wxPython code')

    # start wxPython app
    app = wx.App()
    print('Just before TestFrame().Show()')
    TestFrame().Show()
    print('Just before app.MainLoop()')
    app.MainLoop()
