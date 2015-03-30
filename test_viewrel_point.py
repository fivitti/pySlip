#!/usr/bin/env python

"""Test PySlip view-relative points."""


import wx

import pyslip
import local_tiles


######
# Various demo constants
######

DefaultAppSize = (600, 400)

TileDirectory = 'tiles'
MinTileLevel = 0
InitViewLevel = 2
InitViewPosition = (85.0, -5.0)


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
                          title=('PySlip %s - view-relative point test'
                                 % pyslip.__version__))
        self.SetMinSize(DefaultAppSize)
        self.panel = wx.Panel(self, wx.ID_ANY)
        self.panel.SetBackgroundColour(wx.WHITE)
        self.panel.ClearBackground()

        # create the tile source object
        self.tile_src = local_tiles.LocalTiles(TileDirectory, None)

        # build the GUI
        self.make_gui(self.panel)

        # do initialisation stuff - all the application stuff
        self.init()

        # add test point layers
        self.pyslip.AddPointLayer(PointViewDataNW, placement='nw',
                                  map_rel=False, colour='blue', radius=2,
                                  offset_x=1, offset_y=1,
                                  name='<point_map_layer>')

        self.pyslip.AddPointLayer(PointViewDataCN, placement='cn',
                                  map_rel=False, colour='red', radius=2,
                                  offset_x=1, offset_y=1,
                                  name='<point_map_layer>')

        self.pyslip.AddPointLayer(PointViewDataNE, placement='ne',
                                  map_rel=False, colour='green', radius=2,
                                  offset_x=1, offset_y=1,
                                  name='<point_map_layer>')

        self.pyslip.AddPointLayer(PointViewDataCE, placement='ce',
                                  map_rel=False, colour='black', radius=2,
                                  offset_x=1, offset_y=1,
                                  name='<point_map_layer>')

        self.pyslip.AddPointLayer(PointViewDataSE, placement='se',
                                  map_rel=False, colour='yellow', radius=2,
                                  offset_x=1, offset_y=1,
                                  name='<point_map_layer>')

        self.pyslip.AddPointLayer(PointViewDataCS, placement='cs',
                                  map_rel=False, colour='gray', radius=2,
                                  offset_x=1, offset_y=1,
                                  name='<point_map_layer>')

        self.pyslip.AddPointLayer(PointViewDataSW, placement='sw',
                                  map_rel=False, colour='#7f7fff', radius=2,
                                  offset_x=1, offset_y=1,
                                  name='<point_map_layer>')

        self.pyslip.AddPointLayer(PointViewDataCW, placement='cw',
                                  map_rel=False, colour='#ff7f7f', radius=2,
                                  offset_x=1, offset_y=1,
                                  name='<point_map_layer>')

        self.pyslip.AddPointLayer(PointViewDataCC, placement='cc',
                                  map_rel=False, colour='#7fff7f', radius=2,
                                  offset_x=1, offset_y=1,
                                  name='<point_map_layer>')

        # finally, set up application window position
        self.Centre()

#####
# Build the GUI
#####

    def make_gui(self, parent):
        """Create application GUI."""

        # start application layout
        all_display = wx.BoxSizer(wx.HORIZONTAL)
        parent.SetSizer(all_display)

        # put map view in left of horizontal box
        sl_box = self.make_gui_view(parent)
        all_display.Add(sl_box, proportion=1, border=1, flag=wx.EXPAND)
                        
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

    ######
    # Finish initialization of data, etc
    ######

    def init(self):
        global PointViewDataNW, PointViewDataCN, PointViewDataNE
        global PointViewDataCE, PointViewDataSE, PointViewDataCS
        global PointViewDataSW, PointViewDataCW, PointViewDataCC

        PointViewDataNW = [( 0, 0), ( 2, 0), ( 4, 0), ( 6, 0), ( 8, 0),
                           (10, 0), ( 0, 2), ( 0, 4), ( 0, 6), ( 0, 8),
                           ( 0,10), ( 2, 2), ( 4, 4), ( 6, 6), ( 8, 8),
                           (10,10), (12,12), (14,14), (16,16), (18,18),
                           (20,20)
                          ] 

        PointViewDataCN = [(  0,  0), ( -2,  2), ( -4,  4), ( -6,  6),
                           ( -8,  8), (-10, 10), (  2,  2), (  4,  4),
                           (  6,  6), (  8,  8), ( 10, 10), (  0,  2),
                           (  0,  4), (  0,  6), (  0,  8), (  0, 10),
                           (  0, 12), (  0, 14), (  0, 16), (  0, 18),
                           (  0, 20)
                          ]

        PointViewDataNE = [(  0,  0), ( -2,  0), ( -4,  0), ( -6,  0),
                           ( -8,  0), (-10,  0), (  0,  2), (  0,  4),
                           (  0,  6), (  0,  8), (  0, 10), ( -2,  2),
                           ( -4,  4), ( -6,  6), ( -8,  8), (-10, 10),
                           (-12, 12), (-14, 14), (-16, 16), (-18, 18),
                           (-20, 20)
                          ]

        PointViewDataCE = [(  0,  0), ( -2, -2), ( -4, -4), ( -6, -6),
                           ( -8, -8), (-10,-10), ( -2,  2), ( -4,  4),
                           ( -6,  6), ( -8,  8), (-10, 10), ( -2,  0),
                           ( -4,  0), ( -6,  0), ( -8,  0), (-10,  0),
                           (-12,  0), (-14,  0), (-16,  0), (-18,  0),
                           (-20,  0)
                          ]

        PointViewDataSE = [(  0,  0), (  0, -2), (  0, -4), (  0, -6),
                           (  0, -8), (  0,-10), ( -2,  0), ( -4,  0),
                           ( -6,  0), ( -8,  0), (-10,  0), ( -2, -2),
                           ( -4, -4), ( -6, -6), ( -8, -8), (-10,-10),
                           (-12,-12), (-14,-14), (-16,-16), (-18,-18),
                           (-20,-20)
                          ]

        PointViewDataCS = [(  0,  0), ( -2, -2), ( -4, -4), ( -6, -6),
                           ( -8, -8), (-10,-10), (  2, -2), (  4, -4),
                           (  6, -6), (  8, -8), ( 10,-10), (  0, -2),
                           (  0, -4), (  0, -6), (  0, -8), (  0,-10),
                           (  0,-12), (  0,-14), (  0,-16), (  0,-18),
                           (  0,-20)
                          ]

        PointViewDataSW = [(  0,  0), (  0, -2), (  0, -4), (  0, -6),
                           (  0, -8), (  0,-10), (  2,  0), (  4,  0),
                           (  6,  0), (  8,  0), ( 10,  0), (  2, -2),
                           (  4, -4), (  6, -6), (  8, -8), ( 10,-10),
                           ( 12,-12), ( 14,-14), ( 16,-16), ( 18,-18),
                           ( 20,-20)
                          ]

        PointViewDataCW = [(  0,  0), (  2, -2), (  4, -4), (  6, -6),
                           (  8, -8), ( 10,-10), (  2,  2), (  4,  4),
                           (  6,  6), (  8,  8), ( 10, 10), (  2,  0),
                           (  4,  0), (  6,  0), (  8,  0), ( 10,  0),
                           ( 12,  0), ( 14,  0), ( 16,  0), ( 18,  0),
                           ( 20,  0)
                          ]

        PointViewDataCC = [(  0,  0), (  2, -2), (  4, -4), (  6, -6),
                           (  8, -8), ( 10,-10),
                           (  0,  0), (  2,  2), (  4,  4), (  6,  6),
                           (  8,  8), ( 10, 10),
                           (  0,  0), ( -2, -2), ( -4, -4), ( -6, -6),
                           ( -8, -8), (-10,-10),
                           (  0,  0), ( -2,  2), ( -4,  4), ( -6,  6),
                           ( -8,  8), (-10, 10),
                          ]


        # set initial view position
        self.pyslip.GotoLevelAndPosition(InitViewLevel, InitViewPosition)

        # force pyslip initialisation
        self.pyslip.OnSize()

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

