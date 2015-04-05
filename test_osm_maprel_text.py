#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Test PySlip map-relative text."""


import wx

import pyslip
from osm_tiles import OSMTiles as Tiles


######
# Various demo constants
######

DefaultAppSize = (600, 400)

TileDirectory = './osm_tiles'
MinTileLevel = 0
InitViewLevel = 4
InitViewPosition = (134.0, -25.0)

TextMapData = [(151.20, -33.85, 'Sydney cc', {'placement': 'cc'}),
               (144.95, -37.84, 'Melbourne ne', {'placement': 'ne'}),
               (153.08, -27.48, 'Brisbane ce', {'placement': 'ce'}),
               (115.86, -31.96, 'Perth se', {'placement': 'se'}),
               (138.60, -34.93, 'Adelaide cs', {'placement': 'cs'}),
               (130.83, -12.45, 'Darwin sw', {'placement': 'sw'}),
               (147.33, -42.88, 'Hobart cw', {'placement': 'cw'}),
               (149.20, -35.31, 'Canberra nw', {'placement': 'nw',
                                                'colour': 'red',
                                                'textcolour': 'blue',
                                                'fontsize': 10}),
               (133.90, -23.70, 'Alice Springs cn', {'placement': 'cn'})]


################################################################################
# The main application frame
################################################################################

class TestFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, size=DefaultAppSize,
                          title=('PySlip %s - map-relative text test'
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

        # add test test layer
        self.text_layer = self.pyslip.AddTextLayer(TextMapData,
                                                   map_rel=True,
                                                   name='<text_map_layer>',
                                                   offset_x=5, offset_y=1)

        # set initial view position
        self.pyslip.GotoLevelAndPosition(InitViewLevel, InitViewPosition)

#####
# Build the GUI
#####

    def make_gui(self, parent):
        """Create application GUI."""

        # start application layout
        all_display = wx.BoxSizer(wx.HORIZONTAL)
        parent.SetSizer(all_display)
        self.pyslip = pyslip.PySlip(parent, tile_src=self.tile_src,
                                    min_level=MinTileLevel)
        all_display.Add(self.pyslip, proportion=1, border=1, flag=wx.EXPAND)
        parent.SetSizerAndFit(all_display)

    def make_gui_view(self, parent):
        """Build the map view widget

        parent  reference to the widget parent

        Returns the static box sizer.
        """

        # create gui objects
        sb = AppStaticBox(parent, '')
        self.pyslip = pyslip.PySlip(parent, tile_src=self.tile_src,
                                    min_level=MinTileLevel)

        # lay out objects
        box = wx.StaticBoxSizer(sb, orient=wx.HORIZONTAL)
        box.Add(self.pyslip, proportion=1, border=1, flag=wx.EXPAND)

        return box

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

    # plug our handler into the python system
    sys.excepthook = excepthook

    # start wxPython app
    app = wx.App()
    TestFrame().Show()
    app.MainLoop()

