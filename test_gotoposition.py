#!/usr/bin/env python
# -*- coding= utf-8 -*-

"""
Test PySlip GototPosition() function.

The idea is to have a set of buttons selecting various geo positions on the OSM
tile map.  When selected, the view would be moved with GotoPosition() and a
map-relative marker would be drawn at that position.  At the same time, a
view-relative marker would be drawn at the centre of the view.  The difference
between the two markers shows errors in the Geo2Tile() & Tile2GEO() functions.
"""


import os
import wx
import pyslip
from osm_tiles import OSMTiles as Tiles

# If we have log.py, well and good.  Otherwise ...
try:
    import log
    log = log.Log('pyslip.log', log.Log.DEBUG)
except ImportError:
    def log(*args, **kwargs):
        pass

######
# Various demo constants
######

# demo name/version
DemoVersion = '1.0'
DemoName = "pySlip %s - GotoPosition() test %s" % (pyslip.__version__, DemoVersion)

# initial level and position
InitViewLevel = 3
InitViewPosition = (0.0, 0.0)

# startup size of the application
DefaultAppSize = (800, 665)

# where OSM local tiles live
TileDirectory = 'osm_tiles'

# the number of decimal places in a lon/lat display
LonLatPrecision = 3

# a selection of cities, position from WikiPedia, etc
# format is ((<lon>,<lat>),<name>)
Cities = [((0.0, 51.4778), 'Greenwich, United Kingdom'),
          ((5.33, 60.389444), 'Bergen, Norway'),
          ((151.209444, -33.865), 'Sydney, Australia'),
          ((-77.036667, 38.895111), 'Washington DC, USA'),
          ((132.455278, 34.385278), 'Hiroshima (広島市), Japan'),
          ((-8.008889, 31.63), 'Marrakech (مراكش), Morocco'),
          ((18.95, 69.65), 'Tromsø, Norway'),
          ((-70.933333, -53.166667), 'Punta Arenas, Chile'),
          ((168.3475, -46.413056), 'Invercargill, New Zealand'),
          ((-147.723056, 64.843611), 'Fairbanks AK, USA'),
          ((103.851959, 1.290270), 'Singapore'),
          ((-3.205601, 55.955279), "Maxwell's Birthplace"),
         ]

# sizes of various spacers
HSpacerSize = (3,1)         # horizontal in application screen
VSpacerSize = (1,5)         # vertical in control pane

# border width when packing GUI elements
PackBorder = 1


################################################################################
# Override the wx.TextCtrl class to add read-only style and background colour
################################################################################

# background colour for the 'read-only' text field
ControlReadonlyColour = '#ffffcc'

class ROTextCtrl(wx.TextCtrl):
    """Override the wx.TextCtrl widget to get read-only text control which
    has a distinctive background colour."""

    def __init__(self, parent, value, tooltip='', *args, **kwargs):
        wx.TextCtrl.__init__(self, parent, wx.ID_ANY, value=value,
                             style=wx.TE_READONLY, *args, **kwargs)
        self.SetBackgroundColour(ControlReadonlyColour)
        self.SetToolTip(wx.ToolTip(tooltip))

################################################################################
# Override the wx.StaticBox class to show our style
################################################################################

class AppStaticBox(wx.StaticBox):

    def __init__(self, parent, label, *args, **kwargs):
        if label:
            label = '  ' + label + '  '
        wx.StaticBox.__init__(self, parent, wx.ID_ANY, label, *args, **kwargs)

################################################################################
# The main application frame
################################################################################

class AppFrame(wx.Frame):
    def __init__(self, tile_dir=TileDirectory):
        wx.Frame.__init__(self, None, size=DefaultAppSize, title=DemoName)
        self.SetMinSize(DefaultAppSize)
        self.panel = wx.Panel(self, wx.ID_ANY)
        self.panel.SetBackgroundColour(wx.WHITE)
        self.panel.ClearBackground()

        self.tile_directory = tile_dir
        self.tile_source = Tiles(tile_dir)

        # the data objects for map and view layers
        self.map_layer = None
        self.view_layer = None

        # build the GUI
        self.make_gui(self.panel)

        # finally, set up application window position
        self.Centre()

        # bind events to handlers
        self.pyslip.Bind(pyslip.EVT_PYSLIP_POSITION, self.handle_position_event)
        self.pyslip.Bind(pyslip.EVT_PYSLIP_LEVEL, self.handle_level_change)

        # finally, goto desired level and position
        self.pyslip.GotoLevelAndPosition(InitViewLevel, InitViewPosition)

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

        # small spacer here - separate view and controls
        all_display.AddSpacer(HSpacerSize)

        # add controls to right of spacer
        controls = self.make_gui_controls(parent)
        all_display.Add(controls, proportion=0, border=1)

        parent.SetSizerAndFit(all_display)
#        parent.Fit()

    def make_gui_view(self, parent):
        """Build the map view widget

        parent  reference to the widget parent

        Returns the static box sizer.
        """

        # create gui objects
        sb = AppStaticBox(parent, '')
        tile_object = Tiles(self.tile_directory)
        self.pyslip = pyslip.PySlip(parent, tile_src=self.tile_source)

        # lay out objects
        box = wx.StaticBoxSizer(sb, orient=wx.HORIZONTAL)
        box.Add(self.pyslip, proportion=1, border=1, flag=wx.EXPAND)

        return box

    def make_gui_controls(self, parent):
        """Build the 'controls' part of the GUI

        parent  reference to parent

        Returns reference to containing sizer object.
        """

        # all controls in vertical box sizer
        controls = wx.BoxSizer(wx.VERTICAL)

        # add the map level in use widget
        level = self.make_gui_level(parent)
        controls.Add(level, proportion=0, flag=wx.EXPAND|wx.ALL)

        # vertical spacer
        controls.AddSpacer(VSpacerSize)

        # add the mouse position feedback stuff
        mouse = self.make_gui_mouse(parent)
        controls.Add(mouse, proportion=0, flag=wx.EXPAND|wx.ALL)

        # buttons for each point of interest
        self.buttons = {}
        for (num, city) in enumerate(Cities):
            controls.AddSpacer(VSpacerSize)
            (lonlat, name) = city
            btn = wx.Button(parent, num, name)
            controls.Add(btn, proportion=0, flag=wx.EXPAND|wx.ALL)
            btn.Bind(wx.EVT_BUTTON, self.handle_button)
            self.buttons[num] = city
        return controls

    def make_gui_level(self, parent):
        """Build the control that shows the level.

        parent  reference to parent

        Returns reference to containing sizer object.
        """

        # create objects
        txt = wx.StaticText(parent, wx.ID_ANY, 'Level: ')
        self.map_level = wx.StaticText(parent, wx.ID_ANY, ' ')

        # lay out the controls
        sb = AppStaticBox(parent, 'Map level')
        box = wx.StaticBoxSizer(sb, orient=wx.HORIZONTAL)
        box.Add(txt, border=PackBorder, flag=(wx.ALIGN_CENTER_VERTICAL
                                     |wx.ALIGN_RIGHT|wx.LEFT))
        box.Add(self.map_level, proportion=0, border=PackBorder,
                flag=wx.RIGHT|wx.TOP)

        return box

    def make_gui_mouse(self, parent):
        """Build the mouse part of the controls part of GUI.

        parent  reference to parent

        Returns reference to containing sizer object.
        """

        # create objects
        txt = wx.StaticText(parent, wx.ID_ANY, 'Lon/Lat: ')
        self.mouse_position = ROTextCtrl(parent, '', size=(150,-1),
                                         tooltip=('Shows the mouse '
                                                  'longitude and latitude '
                                                  'on the map'))

        # lay out the controls
        sb = AppStaticBox(parent, 'Mouse position')
        box = wx.StaticBoxSizer(sb, orient=wx.HORIZONTAL)
        box.Add(txt, border=PackBorder, flag=(wx.ALIGN_CENTER_VERTICAL
                                     |wx.ALIGN_RIGHT|wx.LEFT))
        box.Add(self.mouse_position, proportion=1, border=PackBorder,
                flag=wx.RIGHT|wx.TOP|wx.BOTTOM)

        return box

    ######
    # Exception handlers
    ######

    def handle_button(self, event):
        """Handle button event."""

        (posn, name) = self.buttons[event.Id]
        self.pyslip.GotoPosition(posn)

        if self.map_layer:
            self.pyslip.DeleteLayer(self.map_layer)
        map_data = [posn]
        point_colour = '#0000ff40'
        self.map_layer = self.pyslip.AddPointLayer(map_data, map_rel=True,
                                                   placement='cc',
                                                   color=point_colour,
                                                   radius=11,
                                                   visible=True,
                                                   name='map_layer')

        if self.view_layer:
            self.pyslip.DeleteLayer(self.view_layer)
        view_data = [(((0,0),(0,-10),(0,0),(0,10),
            (0,0),(-10,0),(0,0),(10,0)),{'colour':'#ff0000ff'},)]
#        poly_colour = '#ff0000ff'
        self.view_layer = self.pyslip.AddPolygonLayer(view_data, map_rel=False,
                                                      placement='cc',
#                                                      colour=poly_colour,
                                                      closed=False,
                                                      visible=True,
                                                      name='view_layer')

    def handle_position_event(self, event):
        """Handle a pySlip POSITION event."""

        posn_str = ''
        if event.position:
            (lon, lat) = event.position
            posn_str = ('%.*f / %.*f'
                        % (LonLatPrecision, lon, LonLatPrecision, lat))

        self.mouse_position.SetValue(posn_str)

    def handle_level_change(self, event):
        """Handle a pySlip LEVEL event."""

        self.map_level.SetLabel('%d' % event.level)


################################################################################

if __name__ == '__main__':
    import sys
    import traceback
    import tkinter_error

    # our own handler for uncaught exceptions
    def excepthook(type, value, tb):
        msg = '\n' + '=' * 80
        msg += '\nUncaught exception:\n'
        msg += ''.join(traceback.format_exception(type, value, tb))
        msg += '=' * 80 + '\n'
        log(msg)
        tkinter_error.tkinter_error(msg)
        sys.exit(1)

    # use user tile directory, if supplied
    tile_dir = None
    if len(sys.argv) > 1:
        tile_dir = sys.argv[1]

    # plug our handler into the python system
    sys.excepthook = excepthook

    # start wxPython app
    app = wx.App()
    if tile_dir:
        app_frame = AppFrame(tile_dir=tile_dir)
    else:
        app_frame = AppFrame()
    app_frame.Show()

##    import wx.lib.inspection
##    wx.lib.inspection.InspectionTool().Show()

    app.MainLoop()

