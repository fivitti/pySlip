#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Test PySlip with multiple instances.

Usage: test_multi_widget.py [-h]
"""


import wx
import pyslip

from pyslip.gmt_local_tiles import GMTTiles
from pyslip.osm_tiles import OSMTiles


######
# Various demo constants
######

DefaultAppSize = (600, 400)
MinW = 400
MinH = 300
MaxW = 1000
MaxH = 800

MinTileLevel = 0
InitViewLevel = 2
InitViewPosition = (100.51, 13.75)      # Bangkok

################################################################################
# The main application frame
################################################################################

class TestFrame(wx.Frame):
    def __init__(self, gmt_tile_dir, osm_tile_dir):
        """Initialize the widget.

        gmt_tile_dir  path to directory of GMT tiles
        osm_tile_dir  directory for OSM tile caching
        """

        wx.Frame.__init__(self, None, size=DefaultAppSize,
                          title=('PySlip %s - multiwidget test'
                                 % pyslip.__version__))
        self.SetMinSize(DefaultAppSize)
        self.panel = wx.Panel(self, wx.ID_ANY)
        self.panel.SetBackgroundColour(wx.WHITE)
        self.panel.ClearBackground()

        # create the tile source object
        self.gmt_tile_dir = gmt_tile_dir
        self.osm_tile_dir = osm_tile_dir

        # note that we a unique Tile source for each widget
        # sharing directories is OK
        gmt_tile_src_1 = GMTTiles(gmt_tile_dir)
        gmt_tile_src_2 = GMTTiles(gmt_tile_dir)
        osm_tile_src_1 = OSMTiles(osm_tile_dir)
        osm_tile_src_2 = OSMTiles(osm_tile_dir)

        # build the GUI
        box = wx.BoxSizer(wx.VERTICAL)
        gsz = wx.GridSizer(rows=2, cols=2, vgap=5, hgap=5)

        self.pyslip1 = pyslip.PySlip(self.panel, tile_src=gmt_tile_src_1,
                                     min_level=MinTileLevel)
        gsz.Add(self.pyslip1, flag=wx.ALL|wx.EXPAND)

        self.pyslip2 = pyslip.PySlip(self.panel, tile_src=osm_tile_src_1,
                                     min_level=MinTileLevel)
        gsz.Add(self.pyslip2, flag=wx.ALL|wx.EXPAND)

        self.pyslip3 = pyslip.PySlip(self.panel, tile_src=osm_tile_src_2,
                                     min_level=MinTileLevel)
        gsz.Add(self.pyslip3, flag=wx.ALL|wx.EXPAND)

        self.pyslip4 = pyslip.PySlip(self.panel, tile_src=gmt_tile_src_2,
                                     min_level=MinTileLevel)
        gsz.Add(self.pyslip4, flag=wx.ALL|wx.EXPAND)

        box.Add(gsz, proportion=1, flag=wx.ALL|wx.EXPAND)

        self.panel.SetSizer(box)
        self.SetSizeHints(MinW, MinH, MaxW, MaxH)
        self.panel.Fit()
        self.Centre()
        self.Show(True)

        # set initial view position
        self.pyslip1.GotoLevelAndPosition(InitViewLevel, InitViewPosition)
        self.pyslip2.GotoLevelAndPosition(InitViewLevel, InitViewPosition)
        self.pyslip3.GotoLevelAndPosition(InitViewLevel, InitViewPosition)
        self.pyslip4.GotoLevelAndPosition(InitViewLevel, InitViewPosition)

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

    # plug our handler into the python system
    sys.excepthook = excepthook

    # decide which tiles to use, default is GMT
    argv = sys.argv[1:]

    try:
        (opts, args) = getopt.getopt(argv, 'h', ['help'])
    except getopt.error:
        usage()
        sys.exit(1)

    for (opt, param) in opts:
        if opt in ['-h', '--help']:
            usage()
            sys.exit(0)

    # set up the tile sources - GMT and OSM
    gmt_tile_dir = 'gmt_tiles'
    osm_tile_dir = 'osm_tiles'

    # start wxPython app
    app = wx.App()
    TestFrame(gmt_tile_dir, osm_tile_dir).Show()
    app.MainLoop()

