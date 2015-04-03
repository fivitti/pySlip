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
InitViewPosition = (158.0, -20.0)

arrow = 'graphics/arrow_right.png'

ImageMapData = [(158, -17, arrow, {'offset_x': 0, 'offset_y': 0}),
                (158, -18, arrow, {'offset_x': 0, 'offset_y': 0}),
                (158, -19, arrow, {'offset_x': 0, 'offset_y': 0}),
                (158, -20, arrow, {'offset_x': 0, 'offset_y': 0}),
                (158, -21, arrow, {'offset_x': 0, 'offset_y': 0}),
                (158, -22, arrow, {'offset_x': 0, 'offset_y': 0}),
                (158, -23, arrow, {'offset_x': 0, 'offset_y': 0})
               ]

PolygonMapData = [(((158,-17),(158,-23)),
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
                                    min_level=MinTileLevel,
                                    size=DefaultAppSize)
        self.Fit()

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

