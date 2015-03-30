#!/usr/bin/env python

"""Test PySlip 'show_level' feature."""


import wx

import pyslip
import local_tiles
# if we don't have log.py, don't crash
try:
    import log
    log = log.Log('pyslip.log', log.Log.DEBUG)
except ImportError:
    def log(*args, **kwargs):
        pass


######
# Various demo constants
######

DefaultAppSize = (600, 400)

TileDirectory = 'tiles'
MinTileLevel = 0
InitViewLevel = 2
InitViewPosition = (85.0, -5.0)

Instructions = [(2, 2, 'Left click on map to raise text, right to lower',
                 {'placement': 'nw'})]
LevelData = [[(2, 15, 'Text now on level 0', {'placement': 'nw'})],
             [(2, 15, 'Text now on level 1', {'placement': 'nw'})],
             [(2, 15, 'Text now on level 2', {'placement': 'nw'})],
             [(2, 15, 'Text now on level 3', {'placement': 'nw'})],
             [(2, 15, 'Text now on level 4', {'placement': 'nw'})],
             [(2, 15, 'Text now on level 5', {'placement': 'nw'})],
             [(2, 15, 'Text now on level 6', {'placement': 'nw'})],
             [(2, 15, 'Text now on level 7', {'placement': 'nw'})],
             [(2, 15, 'Text now on level 8', {'placement': 'nw'})],
             [(2, 15, 'Text now on level 9', {'placement': 'nw'})]]

TextMapData = [(151.20, -33.85, 'Sydney cc', {'placement': 'cc'}),
               (144.95, -37.84, 'Melbourne ne', {'placement': 'ne'}),
               (153.08, -27.48, 'Brisbane ce', {'placement': 'ce'}),
               (115.86, -31.96, 'Perth se', {'placement': 'se'}),
               (138.30, -35.52, 'Adelaide cs', {'placement': 'cs'}),
               (130.98, -12.61, 'Darwin sw', {'placement': 'sw'}),
               (147.31, -42.96, 'Hobart cw', {'placement': 'cw'}),
               (149.20, -35.31, 'Canberra nw', {'placement': 'nw',
                                                'colour': 'red',
                                                'fontsize': 10}),
               (133.90, -23.70, 'Alice Springs cn', {'placement': 'cn'})]


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
                          title=('PySlip %s - show_level test'
                                 % pyslip.__version__))
        self.SetMinSize(DefaultAppSize)
        self.panel = wx.Panel(self, wx.ID_ANY)
        self.panel.SetBackgroundColour(wx.WHITE)
        self.panel.ClearBackground()

        # build the GUI
        self.make_gui(self.panel)

        # bind click events to handlers
        self.pyslip.Bind(pyslip.EVT_PYSLIP_SELECT, self.OnLeftClick)
        self.pyslip.Bind(pyslip.EVT_PYSLIP_RIGHTSELECT, self.OnRightClick)

        # add instructions and level display
        self.text_level = 2
        self.inst_layer = self.pyslip.AddTextLayer(Instructions,
                                                   map_rel=False,
                                                   selectable=True,
                                                   name='<inst_layer>') 
        self.level_layer = self.pyslip.AddTextLayer(LevelData[self.text_level],
                                                    map_rel=False,
                                                    selectable=False,
                                                    name='<level_layer>') 

        # add test test layer showing at level 2
        self.text_layer = self.pyslip.AddTextLayer(TextMapData,
                                                   map_rel=True,
                                                   show_levels=
                                                       [self.text_level],
                                                   selectable=False,
                                                   name='<text_map_layer>')

        # set initial view position
        self.pyslip.GotoLevelAndPosition(InitViewLevel, InitViewPosition)

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

        # we make the tiles object
        self.tiles = local_tiles.LocalTiles(TileDirectory, None)

        # create gui objects
        sb = AppStaticBox(parent, '')
        self.pyslip = pyslip.PySlip(parent, tile_src=self.tiles,
                                    min_level=MinTileLevel)

        # lay out objects
        box = wx.StaticBoxSizer(sb, orient=wx.HORIZONTAL)
        box.Add(self.pyslip, proportion=1, border=1, flag=wx.EXPAND)

        return box

    def OnLeftClick(self, event):
        """Left click - raise text level if possible."""

        log('OnLeftClick: event.layer_id=%d' % event.layer_id)

        if self.text_level > 0:
            self.text_level -= 1

            self.pyslip.DeleteLayer(self.level_layer)
            data = LevelData[self.text_level]
            self.level_layer = self.pyslip.AddTextLayer(data, map_rel=False,
                                                        selectable=False,
                                                        name='<level_layer>') 

            self.pyslip.DeleteLayer(self.text_layer)
            self.text_layer = self.pyslip.AddTextLayer(TextMapData,
                                                       map_rel=True,
                                                       show_levels=
                                                           [self.text_level],
                                                       selectable=False,
                                                       name='<text_map_layer>')

    def OnRightClick(self, event):
        """Right click - lower text level if possible."""

        log('OnRightClick: event.layer_id=%d' % event.layer_id)

        if self.text_level < self.pyslip.max_level:
            self.text_level += 1

            self.pyslip.DeleteLayer(self.level_layer)
            data = LevelData[self.text_level]
            self.level_layer = self.pyslip.AddTextLayer(data, map_rel=False,
                                                        name='<level_layer>') 

            self.pyslip.DeleteLayer(self.text_layer)
            self.text_layer = self.pyslip.AddTextLayer(TextMapData,
                                                       map_rel=True,
                                                       show_levels=
                                                           [self.text_level],
                                                       name='<text_map_layer>')



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

