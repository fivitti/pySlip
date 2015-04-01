#!/usr/bin/env python

"""Test PySlip view-relative text."""


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
InitViewPosition = (150.0, -25.0)


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
                          title='PySlip view-relative text test')
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
        self.text_layer = self.pyslip.AddTextLayer(TextViewData,
                                                   map_rel=False,
                                                   name='<text_view_layer>',
                                                   offset_x=20, offset_y=20,
                                                   fontsize=20, colour='red')

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
        global TextViewData

        TextViewData = [(  0,   0, 'cc', {'placement':'cc','fontsize':50,'textcolour':'#ff000020'}),
                        (  0,  10, 'cn', {'placement':'cn','fontsize':45,'textcolour':'#00ff0020'}),
                        (-10,  10, 'ne', {'placement':'ne','fontsize':40,'textcolour':'#0000ff20'}),
                        (-10,   0, 'ce', {'placement':'ce','fontsize':35,'textcolour':'#ff000080'}),
                        (-10, -10, 'se', {'placement':'se','fontsize':30,'textcolour':'#00ff0080'}),
                        (  0, -10, 'cs', {'placement':'cs','fontsize':25,'textcolour':'#0000ff80'}),
                        ( 10, -10, 'sw', {'placement':'sw','fontsize':20,'textcolour':'#ff0000ff'}),
                        ( 10,   0, 'cw', {'placement':'cw','fontsize':15,'textcolour':'#00ff00ff'}),
                        ( 10,  10, 'nw', {'placement':'nw','fontsize':10,'textcolour':'#0000ffff'}),
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

