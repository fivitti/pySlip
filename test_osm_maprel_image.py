#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Test PySlip map-relative images."""


import wx

import pyslip
from osm_tiles import OSMTiles as Tiles


######
# Various constants
######

DefaultAppSize = (600, 400)

TileDirectory = './osm_tiles'
MinTileLevel = 0
InitViewLevel = 4
InitViewPosition = (129.0, -20.0)

arrow = 'graphics/arrow_right.png'

ImageMapData = [(129, -17, arrow, {'offset_x': 0, 'offset_y': 0}),
                (129, -18, arrow, {'offset_x': 0, 'offset_y': 0}),
                (129, -19, arrow, {'offset_x': 0, 'offset_y': 0}),
                (129, -20, arrow, {'offset_x': 0, 'offset_y': 0}),
                (129, -21, arrow, {'offset_x': 0, 'offset_y': 0}),
                (129, -22, arrow, {'offset_x': 0, 'offset_y': 0}),
                (129, -23, arrow, {'offset_x': 0, 'offset_y': 0})
               ]

PolygonMapData = [(((129,-17),(129,-23)),
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
        self.panel = wx.Panel(self, wx.ID_ANY)
        self.panel.SetBackgroundColour(wx.WHITE)
        self.panel.ClearBackground()

        # create the tile source object
        self.tile_src = Tiles(TileDirectory)

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

        # add test layers
        self.poly_layer = self.pyslip.AddPolygonLayer(PolygonMapData)
        self.image_layer = self.pyslip.AddImageLayer(ImageMapData,
                                                     map_rel=True,
                                                     placement='ce',
                                                     name='<image_map_layer>')

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

