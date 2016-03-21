#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Test PySlip "zoom cancel" AFTER zoom has occurred.

Usage: test_displayable_levels.py [-h] [-t (OSM|GMT)]
"""


import wx
import pyslip


######
# Various constants
######

DefaultAppSize = (600, 400)

InitViewLevel = 2
InitViewPosition = (158.0, -20.0)

################################################################################
# The main application frame
################################################################################

class TestFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, size=DefaultAppSize,
                          title=('PySlip %s - zoom undo test'
                                 % pyslip.__version__))
        self.SetMinSize(DefaultAppSize)
        self.panel = wx.Panel(self, wx.ID_ANY)
        self.panel.SetBackgroundColour(wx.WHITE)
        self.panel.ClearBackground()

        # create the tile source object
        self.tile_src = Tiles.Tiles()

        # build the GUI
        box = wx.BoxSizer(wx.HORIZONTAL)
        self.panel.SetSizer(box)
        self.pyslip = pyslip.PySlip(self.panel, tile_src=self.tile_src)
        box.Add(self.pyslip, proportion=1, border=1, flag=wx.EXPAND)
        self.panel.SetSizerAndFit(box)
        self.panel.Layout()
        self.Centre()
        self.Show(True)

        # set initial view position
        self.pyslip.GotoLevelAndPosition(InitViewLevel, InitViewPosition)

        # bind the pySlip widget to the "zoom undo" method
        self.pyslip.Bind(pyslip.EVT_PYSLIP_LEVEL, self.onZoom)

    def onZoom(self, event):
        """Catch and undo a zoom.

        Simulate the amount of work a user handler might do before deciding to
        undo a zoom.

        We must check the level we are zooming to.  If we don't, the GotoLevel()
        method below will trigger another exception, which we catch, etc, etc.
        """

        for _ in range(1000):
            pass

        l = [InitViewLevel, InitViewLevel, InitViewLevel, InitViewLevel,
             InitViewLevel, InitViewLevel, InitViewLevel, InitViewLevel,
             InitViewLevel, InitViewLevel, InitViewLevel, InitViewLevel,
             InitViewLevel, InitViewLevel, InitViewLevel, InitViewLevel,
             InitViewLevel, InitViewLevel, InitViewLevel, InitViewLevel,
            ]

        if event.level not in l:
            self.pyslip.GotoLevel(InitViewLevel)

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
        print msg
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
        import pyslip.gmt_local_tiles as Tiles
    elif tile_source == 'osm':
        import pyslip.osm_tiles as Tiles
    else:
        usage('Bad tile source: %s' % tile_source)
        sys.exit(3)

    # start wxPython app
    app = wx.App()
    TestFrame().Show()
    app.MainLoop()

