#!/usr/bin/env python
# -*- coding= utf-8 -*-

"""
pySlip demonstration program containing mutiple instances of the pySlip widget.

Usage: multi_widget.py <options>

where <options> is zero or more of:
    -d|--debug <level>
        where <level> is either a numeric debug level in the range [0, 50] or
        one of the symbolic debug level names:
            NOTSET    0     nothing is logged (default)
            DEBUG    10     everything is logged
            INFO     20     less than DEBUG, informational debugging
            WARNING  30     less than INFO, only non-fatal warnings
            ERROR    40     less than WARNING
            CRITICAL 50     less than ERROR
    -h|--help
        prints this help and stops
    -x|--inspect
        starts the program with the graphics inspector (for debug)

The program will display four pySlip widgets, two using the GMT tileset and the
other Rtwo using OSM tiles from the public servers.
"""


import os
import copy
try:
    from pyslip.tkinter_error import tkinter_error
except ImportError:
    print('*'*60 + '\nSorry, you must install pySlip first\n' + '*'*60)
    raise
try:
    import wx
except ImportError:
    msg = 'Sorry, you must install wxPython'
    tkinter_error(msg)

import pyslip
import pyslip.log as log


######
# Various demo constants
######

# demo name/version
DemoName = 'pySlip %s - Multiwidget Demonstration' % pyslip.__version__
DemoVersion = '3.0'

# tiles info
TileDirectory = 'tiles'
MinTileLevel = 0

# initial view level and position
InitViewLevel = 4

# this will eventually be selectable within the app
# a selection of cities, position from WikiPedia, etc
#InitViewPosition = (0.0, 51.48)             # Greenwich, England
#InitViewPosition = (5.33, 60.389444)        # Bergen, Norway
#InitViewPosition = (153.033333, -27.466667) # Brisbane, Australia
InitViewPosition = (98.3786761, 7.8627326)   # Phuket (ภูเก็ต), Thailand
#InitViewPosition = (151.209444, -33.859972) # Sydney, Australia
#InitViewPosition = (-77.036667, 38.895111)  # Washington, DC, USA
#InitViewPosition = (132.455278, 34.385278)  # Hiroshima (広島市), Japan
#InitViewPosition = (-8.008889, 31.63)       # Marrakech (مراكش), Morocco
#InitViewPosition = (18.95, 69.65)           # Tromsø, Norway
#InitViewPosition = (-70.933333, -53.166667) # Punta Arenas, Chile
#InitViewPosition = (168.3475, -46.413056)   # Invercargill, New Zealand
#InitViewPosition = (-147.723056, 64.843611) # Fairbanks, AK, USA
#InitViewPosition = (103.851959, 1.290270)   # Singapore

# levels on which various layers show
MRPointShowLevels = [3, 4]
MRImageShowLevels = [3, 4]
MRTextShowLevels = None #[3, 4]
MRPolyShowLevels = [3, 4]
MRPolylineShowLevels = [3, 4]

# the number of decimal places in a lon/lat display
LonLatPrecision = 3

# startup size of the application
DefaultAppSize = (1100, 770)

# default deltas for various layer types
DefaultPointMapDelta = 40
DefaultPointViewDelta = 40
DefaultImageMapDelta = 40
DefaultImageViewDelta = 40
DefaultTextMapDelta = 40
DefaultTextViewDelta = 40
DefaultPolygonMapDelta = 40
DefaultPolygonViewDelta = 40
DefaultPolylineMapDelta = 40
DefaultPolylineViewDelta = 40

# image used for shipwrecks, glassy buttons, etc
ShipImg = 'graphics/shipwreck.png'

GlassyImg2 = 'graphics/glassy_button_2.png'
SelGlassyImg2 = 'graphics/selected_glassy_button_2.png'
GlassyImg3 = 'graphics/glassy_button_3.png'
SelGlassyImg3 = 'graphics/selected_glassy_button_3.png'
GlassyImg4 = 'graphics/glassy_button_4.png'
SelGlassyImg4 = 'graphics/selected_glassy_button_4.png'
GlassyImg5 = 'graphics/glassy_button_5.png'
SelGlassyImg5 = 'graphics/selected_glassy_button_5.png'
GlassyImg6 = 'graphics/glassy_button_6.png'
SelGlassyImg6 = 'graphics/selected_glassy_button_6.png'

# image used for shipwrecks
CompassRoseGraphic = 'graphics/compass_rose.png'

# logging levels, symbolic to numeric mapping
LogSym2Num = {'CRITICAL': 50,
              'ERROR': 40,
              'WARNING': 30,
              'INFO': 20,
              'DEBUG': 10,
              'NOTSET': 0}

######
# Various GUI layout constants
######

# border width when packing GUI elements
PackBorder = 0


###############################################################################
# Override the wx.TextCtrl class to add read-only style and background colour
###############################################################################

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

###############################################################################
# Override the wx.StaticBox class to show our style
###############################################################################

class AppStaticBox(wx.StaticBox):

    def __init__(self, parent, label, *args, **kwargs):
        if label:
            label = '  ' + label + '  '
        if 'style' not in kwargs:
            kwargs['style'] = wx.NO_BORDER
        wx.StaticBox.__init__(self, parent, wx.ID_ANY, label, *args, **kwargs)

###############################################################################
# Class for a PyslipWidget widget.
#
# This is used to control each type of layer, whether map- or view-relative.
###############################################################################

myEVT_ONOFF = wx.NewEventType()
myEVT_SHOWONOFF = wx.NewEventType()
myEVT_SELECTONOFF = wx.NewEventType()

EVT_ONOFF = wx.PyEventBinder(myEVT_ONOFF, 1)
EVT_SHOWONOFF = wx.PyEventBinder(myEVT_SHOWONOFF, 1)
EVT_SELECTONOFF = wx.PyEventBinder(myEVT_SELECTONOFF, 1)

class PyslipWidgetEvent(wx.PyCommandEvent):
    """Event sent when a PyslipWidget is changed."""

    def __init__(self, eventType, id):
        wx.PyCommandEvent.__init__(self, eventType, id)

class PyslipWidget(wx.Panel):

    def __init__(self, parent, title, selectable=False, editable=False,
                 **kwargs):
        """Initialise a PyslipWidget instance.

        parent      reference to parent object
        title       text to ahow in static box outline
        selectable  True if 'selectable' checkbox is to be displayed
        editable    True if layer can be edited
        **kwargs    keyword args for Panel
        """

        # create and initialise the base panel
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY, **kwargs)
        self.SetBackgroundColour(wx.WHITE)

        self.selectable = selectable
        self.editable = editable

        box = AppStaticBox(self, title)
        sbs = wx.StaticBoxSizer(box, orient=wx.VERTICAL)
        gbs = wx.GridBagSizer(vgap=0, hgap=0)

        self.cbx_onoff = wx.CheckBox(self, wx.ID_ANY, label='Add layer')
        gbs.Add(self.cbx_onoff, (0,0), span=(1,4), border=PackBorder)

        self.cbx_show = wx.CheckBox(self, wx.ID_ANY, label='Show')
        gbs.Add(self.cbx_show, (1,1), border=PackBorder)
        self.cbx_show.Disable()

        if selectable:
            self.cbx_select = wx.CheckBox(self, wx.ID_ANY, label='Select')
            gbs.Add(self.cbx_select, (1,2), border=PackBorder)
            self.cbx_select.Disable()

        if editable:
            self.cbx_edit = wx.CheckBox(self, wx.ID_ANY, label='Edit')
            gbs.Add(self.cbx_edit, (1,3), border=PackBorder)
            self.cbx_edit.Disable()

        sbs.Add(gbs)
        self.SetSizer(sbs)
        sbs.Fit(self)

        # tie handlers to change events
        self.cbx_onoff.Bind(wx.EVT_CHECKBOX, self.onChangeOnOff)
        self.cbx_show.Bind(wx.EVT_CHECKBOX, self.onChangeShowOnOff)
        if selectable:
            self.cbx_select.Bind(wx.EVT_CHECKBOX, self.onChangeSelectOnOff)
#        if editable:
#            self.cbx_edit.Bind(wx.EVT_CHECKBOX, self.onChangeEditOnOff)

    def onChangeOnOff(self, event):
        """Main checkbox changed."""

        event = PyslipWidgetEvent(myEVT_ONOFF, self.GetId())
        event.state = self.cbx_onoff.IsChecked()
        self.GetEventHandler().ProcessEvent(event)

        if self.cbx_onoff.IsChecked():
            self.cbx_show.Enable()
            self.cbx_show.SetValue(True)
            if self.selectable:
                self.cbx_select.Enable()
                self.cbx_select.SetValue(False)
            if self.editable:
                self.cbx_edit.Enable()
                self.cbx_edit.SetValue(False)
        else:
            self.cbx_show.Disable()
            if self.selectable:
                self.cbx_select.Disable()
            if self.editable:
                self.cbx_edit.Disable()

    def onChangeShowOnOff(self, event):
        """Show checkbox changed."""

        event = PyslipWidgetEvent(myEVT_SHOWONOFF, self.GetId())
        event.state = self.cbx_show.IsChecked()
        self.GetEventHandler().ProcessEvent(event)

    def onChangeSelectOnOff(self, event):
        """Select checkbox changed."""

        event = PyslipWidgetEvent(myEVT_SELECTONOFF, self.GetId())
        if self.selectable:
            event.state = self.cbx_select.IsChecked()
        else:
            event_state = False
        self.GetEventHandler().ProcessEvent(event)

###############################################################################
# Override the wx.TextCtrl class to add read-only style and background colour
###############################################################################

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

###############################################################################
# Override the wx.StaticBox class to show our style
###############################################################################

class AppStaticBox(wx.StaticBox):

    def __init__(self, parent, label, *args, **kwargs):
        if label:
            label = '  ' + label + '  '
        if 'style' not in kwargs:
            kwargs['style'] = wx.NO_BORDER
        wx.StaticBox.__init__(self, parent, wx.ID_ANY, label, *args, **kwargs)

###############################################################################
# Create a class for the four pyslip widgets.
# Must take tile source as a parameter.
###############################################################################

class PyslipWidget(wx.Panel):

    def __init__(self, parent, title, tile_source, **kwargs):
        """Initialise a PyslipWidget instance.

        parent       reference to parent object
        title        text to ahow in static box outline
        tile_source  source of tiles for this widget
        **kwargs     keyword args for Panel
        """

        # create and initialise the base panel
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY, **kwargs)
        self.SetBackgroundColour(wx.WHITE)

        box = AppStaticBox(self, title)
        sbs = wx.StaticBoxSizer(box, orient=wx.VERTICAL)

        # put in the pySlip widget
        self.pyslip = pyslip.PySlip(parent, tile_src=tile_source,
                                    min_level=MinTileLevel)

        self.SetSizer(sbs)
        sbs.Fit(self)


###############################################################################
# The main application frame
###############################################################################

class AppFrame(wx.Frame):
    def __init__(self, gmt_tile_dir, osm_tile_dir):
        wx.Frame.__init__(self, None, size=DefaultAppSize,
                          title='%s %s' % (DemoName, DemoVersion))
        self.SetMinSize(DefaultAppSize)
        self.panel = wx.Panel(self, wx.ID_ANY)
        self.panel.SetBackgroundColour(wx.WHITE)
        self.panel.ClearBackground()

        self.gmt_tile_directory = gmt_tile_dir
        self.osm_tile_directory = osm_tile_dir
        self.gmt_tile_source = GMTTiles(gmt_tile_dir)
        self.osm_tile_source = OSMTiles(osm_tile_dir)

        # build the GUI
        self.make_gui(self.panel)

        # finally, set up application window position
        self.Centre()

        # create select event dispatch directory
        self.demo_select_dispatch = {}

        # finally, bind events to handlers
#        self.pyslip.Bind(pyslip.EVT_PYSLIP_SELECT, self.handle_select_event)
#        self.pyslip.Bind(pyslip.EVT_PYSLIP_BOXSELECT, self.handle_select_event)
#        self.pyslip.Bind(pyslip.EVT_PYSLIP_POSITION, self.handle_position_event)
#        self.pyslip.Bind(pyslip.EVT_PYSLIP_LEVEL, self.handle_level_change)

#####
# Build the GUI
#####

    def make_gui(self, parent):
        """Create application GUI."""

        # start application layout
        #all_display = wx.BoxSizer(wx.HORIZONTAL)
        all_display = wx.GridBagSizer(vgap=0, hgap=0)
        parent.SetSizer(all_display)

        # put GMT widgets in top-left and bottom-right holes
        self.gmt_widget_1 = PyslipWidget(parent, 'GMT tiles')
        gbs.Add(self.gmt_widget_1, (0,0), border=5)
        self.gmt_widget_2 = PyslipWidget(parent, 'GMT tiles')
        gbs.Add(self.gmt_widget_2, (1,1), border=5)

        self.osm_widget_1 = PyslipWidget(parent, 'OSM tiles')
        gbs.Add(self.osm_widget_1, (0,1), border=5)
        self.osm_widget_2 = PyslipWidget(parent, 'OSM tiles')
        gbs.Add(self.osm_widget_2, (1,0), border=5)

        parent.SetSizerAndFit(all_display)

    ######
    # Small utility routines
    ######

    def unimplemented(self, msg):
        """Issue an "Sorry, ..." message."""

        self.pyslip.warn('Sorry, %s is not implemented at the moment.' % msg)


    ######
    # Finish initialization of data, etc
    ######

        """Perform final setup.

        level     zoom level required
        position  position to be in centre of view

        We do this in a CallAfter() function for those operations that
        must not be done while the GUI is "fluid".
        """

        self.gmt_widget_1.GotoLevelAndPosition(level, position)
        self.gmt_widget_2.GotoLevelAndPosition(level, position)
        self.osm_widget_1.GotoLevelAndPosition(level, position)
        self.osm_widget_2.GotoLevelAndPosition(level, position)

###############################################################################

if __name__ == '__main__':
    import sys
    import getopt
    import traceback

    # our own handler for uncaught exceptions
    def excepthook(type, value, tb):
        msg = '\n' + '=' * 80
        msg += '\nUncaught exception:\n'
        msg += ''.join(traceback.format_exception(type, value, tb))
        msg += '=' * 80 + '\n'
        log(msg)
        tkinter_error(msg)
        sys.exit(1)

    def usage(msg=None):
        if msg:
            print(('*'*80 + '\n%s\n' + '*'*80) % msg)
        print(__doc__)


    # plug our handler into the python system
    sys.excepthook = excepthook

    # decide which tiles to use, default is GMT
    argv = sys.argv[1:]

    try:
        (opts, args) = getopt.getopt(argv, 'd:ht:',
                                           ['debug=', 'help', 'tiles='])
    except getopt.error:
        usage()
        sys.exit(1)

    debug = 0              # no logging
    tile_source = 'GMT'
    inspector = False

    for (opt, param) in opts:
        if opt in ['-d', '--debug']:
            debug = param
        elif opt in ['-h', '--help']:
            usage()
            sys.exit(0)
        elif opt in ('-x', '--inspect'):
            inspector = True

    tile_source = tile_source.lower()

    # convert any symbolic debug level to a number
    try:
        debug = int(debug)
    except ValueError:
        # possibly a symbolic debug name
        try:
            debug = LogSym2Num[debug.upper()]
        except KeyError:
            usage('Unrecognized debug name: %s' % debug)
            sys.exit(1)
    log.set_level(debug)

    # set up the tile sources
    from pyslip.gmt_local_tiles import GMTTiles
    gmt_tile_dir = 'gmt_tiles'

    from pyslip.osm_tiles import OSMTiles
    osm_tile_dir = 'osm_tiles'

    # start wxPython app
    app = wx.App()
    app_frame = AppFrame(gmt_tile_dir=gmt_tile_dir, osm_tile_dir=osm_tile_dir)
    app_frame.Show()

    if inspector:
        import wx.lib.inspection
        wx.lib.inspection.InspectionTool().Show()

    app.MainLoop()

