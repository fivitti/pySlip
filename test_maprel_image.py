#!/usr/bin/env python

"""Test PySlip map-relative images."""


import wx

import pyslip
from gmt_local_tiles import GMTTiles as Tiles


######
# Various constants
######

DefaultAppSize = (600, 400)

TileDirectory = 'tiles'
MinTileLevel = 0
InitViewLevel = 2
InitViewPosition = (133.0, -27.0)

arrow = 'graphics/arrow_right.png'

ImageMapData = [(130, -21, arrow, {'offset_x':   0, 'offset_y': 0}),
                (130, -22, arrow, {'offset_x':  -5, 'offset_y': 0}),
                (130, -23, arrow, {'offset_x': -10, 'offset_y': 0}),
                (130, -24, arrow, {'offset_x': -15, 'offset_y': 0}),
                (130, -25, arrow, {'offset_x': -20, 'offset_y': 0}),
                (130, -26, arrow, {'offset_x': -25, 'offset_y': 0}),
                (130, -27, arrow, {'offset_x': -30, 'offset_y': 0})
               ]

PolygonMapData = [(((130,-21),(130,-27)),
                      {'width': 1, 'colour': 'black', 'filled': False})
                 ]

################################################################################
# The main application frame
################################################################################

class TestFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, size=DefaultAppSize,
                          title=('PySlip %s - map-relative image test'
                                 % pyslip.__version__))
        self.SetMinSize(DefaultAppSize)

        # create the tile source object
        self.tile_src = Tiles(TileDirectory)

        # create the PySlip widget
        self.pyslip = pyslip.PySlip(self, tile_src=self.tile_src,
                                    min_level=MinTileLevel)

        # set initial view position
        self.pyslip.GotoLevelAndPosition(InitViewLevel, InitViewPosition)

        # add test layers
        self.poly_layer = self.pyslip.AddPolygonLayer(PolygonMapData)
        self.image_layer = self.pyslip.AddImageLayer(ImageMapData,
                                                     map_rel=True,
                                                     placement='ce',
                                                     name='<image_map_layer>')

        # finally, set up application window position
        self.Centre()

################################################################################

if __name__ == '__main__':
    import sys
    import traceback

    # our own handler for uncaught exceptions
    def excepthook(type, value, tb):
        msg = '\n' + '=' * 80
        msg += '\nUncaught exception:\n'
        msg += ''.join(traceback.format_exception(type, value, tb))
        msg += '=' * 80 + '\n'
        print msg
        sys.exit(1)
    sys.excepthook = excepthook

    # start wxPython app
    app = wx.App()
    TestFrame().Show()
    app.MainLoop()

