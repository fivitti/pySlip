#!/usr/bin/env python

"""Test PySlip map-relative polygons."""


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
InitViewPosition = (145.0, -10.0)


################################################################################
# Override the wx.StaticBox class to show our style
################################################################################

class AppStaticBox(wx.StaticBox):
    
    def __init__(self, parent, label, *args, **kwargs):
        if label:
            label = '  ' + label + '  '
        wx.StaticBox.__init__(self, parent, wx.ID_ANY, label,
                              *args, **kwargs)
                                            
################################################################################
# The main application frame
################################################################################

class TestFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, size=DefaultAppSize,
                          title=('PySlip %s - map-relative polygon test'
                                 % pyslip.__version__))
        self.SetMinSize(DefaultAppSize)

        # create the tile source object
        self.tile_src = Tiles(TileDirectory)

        # create gui objects
        self.pyslip = pyslip.PySlip(self, tile_src=self.tile_src,
                                    min_level=MinTileLevel,
                                    size=DefaultAppSize)
        self.Fit()

        # create polygon data
        open_poly = ((145,5),(135,5),(135,-5),(145,-5))
        closed_poly = ((145,-20),(135,-20),(135,-10),(145,-10))
        filled_poly = ((170,-20),(160,-20),(160,-10),(170,-10))
        closed_filled_poly = ((170,5),(160,5),(160,-5),(170,-5))

        polymapdata = [[open_poly, {'width': 2}],
                       [closed_poly, {'width': 10, 'color': '#00ff0040',
                                      'closed': True}],
                       [filled_poly, {'colour': 'blue',
                                      'filled': True,
                                      'fillcolour': '#00ff0022'}],
                       [closed_filled_poly, {'colour': 'black',
                                             'closed': True,
                                             'filled': True,
                                             'fillcolour': 'yellow'}]]

        textmapdata = [(135, 5, 'open', {'placement': 'ce'}),
                       (135, -10, 'closed', {'placement': 'ce'}),
                       (170, -10, 'open but filled (translucent)', {'placement': 'cw'}),
                       (170, 5, 'closed & filled (solid)', {'placement': 'cw'}),
                      ]

        # set initial view position
        self.pyslip.GotoLevelAndPosition(InitViewLevel, InitViewPosition)

        # add test text layer
        self.poly_layer = self.pyslip.AddPolygonLayer(polymapdata,
                                                      map_rel=True,
                                                      name='<poly_map_layer>',
                                                      size=DefaultAppSize)
        self.text_layer = self.pyslip.AddTextLayer(textmapdata, map_rel=True,
                                                   name='<text_map_layer>')


        # finally, set up application window position
        self.Centre()
        self.Show(True)

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

