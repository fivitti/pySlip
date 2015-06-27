#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Test PySlip map-relative polygons.

Usage: test_maprel_poly.py [-h] [-t (OSM|GMT)]
"""


import wx
import pyslip


######
# Various demo constants
######

DefaultAppSize = (600, 400)

MinTileLevel = 0
InitViewLevel = 2
InitViewPosition = (152.0, -8.0)

# create polygon data
OpenPoly = ((145,5),(135,5),(135,-5),(145,-5))
ClosedPoly = ((170,5),(160,5),(160,-5),(170,-5))
FilledPoly = ((170,-20),(160,-20),(160,-10),(170,-10))
ClosedFilledPoly = ((145,-20),(135,-20),(135,-10),(145,-10))

PolyMapData = [[OpenPoly, {'width': 2}],
               [ClosedPoly, {'width': 10, 'color': '#00ff0040',
                             'closed': True}],
               [FilledPoly, {'colour': 'blue',
                             'filled': True,
                             'fillcolour': '#00ff0022'}],
               [ClosedFilledPoly, {'colour': 'black',
                                   'closed': True,
                                   'filled': True,
                                   'fillcolour': 'yellow'}]]

TextMapData = [(135, 5, 'open', {'placement': 'ce', 'radius': 0}),
               (170, 5, 'closed', {'placement': 'cw', 'radius': 0}),
               (170, -10, 'open but filled (translucent)',
                   {'placement': 'cw', 'radius': 0}),
               (135, -10, 'closed & filled (solid)',
                   {'placement': 'ce', 'radius': 0}),
              ]


################################################################################
# The main application frame
################################################################################

class TestFrame(wx.Frame):
    def __init__(self, tile_dir):
        wx.Frame.__init__(self, None, size=DefaultAppSize,
                          title=('PySlip %s - map-relative polygon test'
                                 % pyslip.__version__))
        self.SetMinSize(DefaultAppSize)
        self.panel = wx.Panel(self, wx.ID_ANY)
        self.panel.SetBackgroundColour(wx.WHITE)
        self.panel.ClearBackground()

        # create the tile source object
        self.tile_src = Tiles(tile_dir)

        # build the GUI
        box = wx.BoxSizer(wx.HORIZONTAL)
        self.panel.SetSizer(box)
        self.pyslip = pyslip.PySlip(self.panel, tile_src=self.tile_src,
                                    min_level=MinTileLevel)
        box.Add(self.pyslip, proportion=1, border=1, flag=wx.EXPAND)
        self.panel.SetSizerAndFit(box)
        self.panel.Layout()
        self.Centre()
        self.Show(True)

        # set initial view position
        self.pyslip.GotoLevelAndPosition(InitViewLevel, InitViewPosition)

        # add test text layer
        self.poly_layer = self.pyslip.AddPolygonLayer(PolyMapData,
                                                      map_rel=True,
                                                      name='<poly_map_layer>',
                                                      size=DefaultAppSize)
        self.text_layer = self.pyslip.AddTextLayer(TextMapData, map_rel=True,
                                                   name='<text_map_layer>')

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
    TestFrame(tile_dir=tile_dir).Show()
    app.MainLoop()

