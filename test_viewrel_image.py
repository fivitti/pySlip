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
                          title=('PySlip %s - view-relative image test'
                                 % pyslip.__version__))
        self.SetMinSize(DefaultAppSize)
        self.panel = wx.Panel(self, wx.ID_ANY)
        self.panel.SetBackgroundColour(wx.WHITE)
        self.panel.ClearBackground()

        # create the tile source object
        self.tile_src = Tiles(TileDirectory, None)

        # build the GUI
        self.make_gui(self.panel)

        # do initialisation stuff - all the application stuff
        self.init()

        # add test test layer
        self.text_layer = self.pyslip.AddImageLayer(ImageViewData,
                                                    map_rel=False,
                                                    name='<image_view_layer>',
                                                    offset_x=5, offset_y=5)

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
        global ImageViewData

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

