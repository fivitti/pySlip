#!/usr/bin/env python

"""Test PySlip map-relative polygons."""


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
InitViewPosition = (105.0, 20.0)


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
        self.panel = wx.Panel(self, wx.ID_ANY)
        self.panel.SetBackgroundColour(wx.WHITE)
        self.panel.ClearBackground()

        # build the GUI
        self.make_gui(self.panel)

        # do initialisation stuff - all the application stuff
        self.init()

        # add test text layer
        self.poly_layer = self.pyslip.AddPolygonLayer(PolyMapData,
                                                      map_rel=True,
                                                      name='<poly_map_layer>')
        self.text_layer = self.pyslip.AddTextLayer(TextMapData, map_rel=True,
                                                   name='<text_map_layer>')


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

        # create the tile source object
        self.tile_src = local_tiles.LocalTiles(TileDirectory, None)

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
        global PolyMapData, TextMapData

        open_poly = ((145,5),(135,5),(135,-5),(145,-5))
        closed_poly = ((145,-20),(135,-20),(135,-10),(145,-10))
        filled_poly = ((170,-20),(160,-20),(160,-10),(170,-10))
        closed_filled_poly = ((170,5),(160,5),(160,-5),(170,-5))

        PolyMapData = [[open_poly, {'width': 2}],
                       [closed_poly, {'width': 10, 'color': '#00ff0040',
                                      'closed': True}],
                       [filled_poly, {'colour': 'blue',
                                      'filled': True,
                                      'fillcolour': '#00ff0022'}],
                       [closed_filled_poly, {'colour': 'black',
                                             'closed': True,
                                             'filled': True,
                                             'fillcolour': 'yellow'}]]

        TextMapData = [(135, 5, 'open', {'placement': 'ce'}),
                       (135, -10, 'closed', {'placement': 'ce'}),
                       (170, -10, 'open but filled (translucent)', {'placement': 'cw'}),
                       (170, 5, 'closed & filled (solid)', {'placement': 'cw'}),
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

