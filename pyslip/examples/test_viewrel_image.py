#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Test PySlip view-relative images.

Usage: test_maprel_image.py [-h] [-t (OSM|GMT)]
"""


import wx
import pyslip


######
# Various demo constants
######

DefaultAppSize = (600, 400)

MinTileLevel = 0
InitViewLevel = 2
InitViewPosition = (133.87, -23.7)      # Alice Springs

arrow_cw = 'graphics/arrow_left.png'
arrow_nw = 'graphics/arrow_leftup.png'
arrow_cn = 'graphics/arrow_up.png'
arrow_ne = 'graphics/arrow_rightup.png'
arrow_ce = 'graphics/arrow_right.png'
arrow_se = 'graphics/arrow_rightdown.png'
arrow_cs = 'graphics/arrow_down.png'
arrow_sw = 'graphics/arrow_leftdown.png'

ImageViewData = [(0, 0, arrow_cw, {'placement': 'cw'}),
                 (0, 0, arrow_nw, {'placement': 'nw'}),
                 (0, 0, arrow_cn, {'placement': 'cn'}),
                 (0, 0, arrow_ne, {'placement': 'ne'}),
                 (0, 0, arrow_ce, {'placement': 'ce'}),
                 (0, 0, arrow_se, {'placement': 'se'}),
                 (0, 0, arrow_cs, {'placement': 'cs'}),
                 (0, 0, arrow_sw, {'placement': 'sw'}),
                ]


################################################################################
# The main application frame
################################################################################

class TestFrame(wx.Frame):
    def __init__(self, tile_dir):
        wx.Frame.__init__(self, None, size=DefaultAppSize,
                          title=('PySlip %s - view-relative image test'
                                 % pyslip.__version__))
        self.SetMinSize(DefaultAppSize)
        self.panel = wx.Panel(self, wx.ID_ANY)
        self.panel.SetBackgroundColour(wx.WHITE)
        self.panel.ClearBackground()

        # create the tile source object
        self.tile_src = Tiles(tile_dir)

        # build the GUI
        box = wx.BoxSizer(wx.VERTICAL)
        self.pyslip = pyslip.PySlip(self.panel, tile_src=self.tile_src,
                                    min_level=MinTileLevel)
        box.Add(self.pyslip, proportion=1, border=1, flag=wx.EXPAND)
        self.panel.SetSizer(box)
        self.panel.Layout()
        self.Centre()
        self.Show(True)

        # set initial view position and add test layer(s)
        self.pyslip.GotoLevelAndPosition(InitViewLevel, InitViewPosition)
        self.text_layer = self.pyslip.AddImageLayer(ImageViewData,
                                                    map_rel=False,
                                                    name='<image_view_layer>',
                                                    offset_x=0, offset_y=0)

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
        from pyslip.gmt_local_tiles import GMTTiles as Tiles
        tile_dir = 'gmt_tiles'
    elif tile_source == 'osm':
        from pyslip.osm_tiles import OSMTiles as Tiles
        tile_dir = 'osm_tiles'
    else:
        usage('Bad tile source: %s' % tile_source)
        sys.exit(3)

    # start wxPython app
    app = wx.App()
    TestFrame(tile_dir).Show()
    app.MainLoop()

