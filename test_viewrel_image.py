#!/usr/bin/env python

"""Test PySlip view-relative images."""


import wx

import pyslip
from gmt_local_tiles import GMTTiles as Tiles


######
# Various demo constants
######

DefaultAppSize = (600, 400)

TileDirectory = 'tiles'
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
    def __init__(self):
        wx.Frame.__init__(self, None, size=DefaultAppSize,
                          title=('PySlip %s - view-relative image test'
                                 % pyslip.__version__))
        self.SetMinSize(DefaultAppSize)
        self.panel = wx.Panel(self, wx.ID_ANY)
        self.panel.SetBackgroundColour(wx.WHITE)
        self.panel.ClearBackground()

        # create the tile source object
        self.tile_src = Tiles(TileDirectory, None)

        # build the GUI                                                                                                             
        box = wx.BoxSizer(wx.HORIZONTAL)                                                                                            
        self.panel.SetSizer(box)                                                                                                    
        self.pyslip = pyslip.PySlip(self.panel, tile_src=self.tile_src,                                                             
                                    min_level=MinTileLevel)                                                                         
        box.Add(self.pyslip, proportion=1, border=1, flag=wx.EXPAND)                                                                
        self.panel.SetSizerAndFit(box)                                                                                              

        # set initial view position
        self.pyslip.GotoLevelAndPosition(InitViewLevel, InitViewPosition)

        # add test test layer
        self.text_layer = self.pyslip.AddImageLayer(ImageViewData,
                                                    map_rel=False,
                                                    name='<image_view_layer>',
                                                    offset_x=0, offset_y=0)

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

    # plug our handler into the python system
    sys.excepthook = excepthook

    # start wxPython app
    app = wx.App()
    TestFrame().Show()
    app.MainLoop()

