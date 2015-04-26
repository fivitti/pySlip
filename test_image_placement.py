#!/usr/bin/env python
# -*- coding= utf-8 -*-

"""
Program to test image map-relative and view-relative placement.
Select which to show and experiment with placement parameters.

Usage: test_image_placement.py [-h|--help] [-d] [(-t|--tiles) (GMT|OSM)]
"""


import os
import tkinter_error
try:
    import wx
except ImportError:
    msg = 'Sorry, you must install wxPython'
    tkinter_error.tkinter_error(msg)

# If we have log.py, well and good.  Otherwise ...
try:
    import log
    log = log.Log('pyslip.log', log.Log.DEBUG)
except ImportError:
    def log(*args, **kwargs):
        pass

import pyslip


######
# Various demo constants
######

# demo name/version
DemoName = 'Test image placement, pySlip %s' % pyslip.__version__
DemoVersion = '1.0'

# initial values
InitialViewLevel = 4
InitialViewPosition = (145.0, -20.0)

# tiles info
TileDirectory = 'tiles'
MinTileLevel = 0

# the number of decimal places in a lon/lat display
LonLatPrecision = 3

# startup size of the application
DefaultAppSize = (1000, 700)

# initial values in map-relative LayerControl
DefaultFilename = 'graphics/shipwreck.png'
DefaultPlacement = 'ne'
DefaultX = 145.0
DefaultY = -20.0
DefaultOffsetX = 0
DefaultOffsetY = 0

# initial values in view-relative LayerControl
DefaultViewFilename = 'graphics/compass_rose.png'
DefaultViewPlacement = 'ne'
DefaultViewX = 0
DefaultViewY = 0
DefaultViewOffsetX = 0
DefaultViewOffsetY = 0

######
# Various GUI layout constants
######

# sizes of various spacers
HSpacerSize = (0,1)         # horizontal in application screen
VSpacerSize = (1,1)         # vertical in control pane

# border width when packing GUI elements
PackBorder = 0

# various GUI element sizes
FilenameBoxSize = (160, 25)
PlacementBoxSize = (60, 25)
OffsetBoxSize = (60, 25)


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
        if 'style' not in kwargs:
            kwargs['style'] = wx.NO_BORDER
        wx.StaticBox.__init__(self, parent, wx.ID_ANY, label, *args, **kwargs)

###############################################################################
# Class for a LayerControl widget.
#
# This is used to control each type of layer, whether map- or view-relative.
###############################################################################

myEVT_DELETE = wx.NewEventType()
myEVT_UPDATE = wx.NewEventType()

EVT_DELETE = wx.PyEventBinder(myEVT_DELETE, 1)
EVT_UPDATE = wx.PyEventBinder(myEVT_UPDATE, 1)

class LayerControlEvent(wx.PyCommandEvent):
    """Event sent when a LayerControl is changed."""

    def __init__(self, eventType, id):
        wx.PyCommandEvent.__init__(self, eventType, id)

class LayerControl(wx.Panel):

    def __init__(self, parent, title, filename='', placement=DefaultPlacement,
                 x=0, y=0, offset_x=0, offset_y=0, **kwargs):
        """Initialise a LayerControl instance.

        parent      reference to parent object
        title       text to show in static box outline
        filename    filename of image to show
        placement   placement string for image
        x, y        X and Y coords
        offset_x    X offset of image
        offset_y    Y offset of image
        **kwargs    keyword args for Panel
        """

        # create and initialise the base panel
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY, **kwargs)
        self.SetBackgroundColour(wx.WHITE)

        self.v_filename = filename
        self.v_placement = placement
        self.v_x = x
        self.v_y = y
        self.v_offset_x = offset_x
        self.v_offset_y = offset_y

        box = AppStaticBox(self, title)
        sbs = wx.StaticBoxSizer(box, orient=wx.VERTICAL)
        gbs = wx.GridBagSizer(vgap=2, hgap=2)

        label = wx.StaticText(self, wx.ID_ANY, 'filename: ')
        gbs.Add(label, (0,0), border=0,
                flag=(wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT))
        self.filename = ROTextCtrl(self, self.v_filename, size=FilenameBoxSize)
        gbs.Add(self.filename, (0,1), span=(1,3), border=0, flag=wx.EXPAND)

        label = wx.StaticText(self, wx.ID_ANY, 'placement: ')
        gbs.Add(label, (1,0), border=0,
                flag=(wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT))
        choices = ['nw', 'cn', 'ne', 'ce', 'se', 'cs', 'sw', 'cw', 'cc', 'none']
        style=wx.CB_DROPDOWN|wx.CB_READONLY
        self.placement = wx.ComboBox(self, value=self.v_placement,
                                     size=PlacementBoxSize,
                                     choices=choices, style=style)
        gbs.Add(self.placement, (1,1), border=0)

        label = wx.StaticText(self, wx.ID_ANY, 'x: ')
        gbs.Add(label, (2,0), border=0,
                flag=(wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT))
        self.x = wx.TextCtrl(self, value=str(self.v_x), size=OffsetBoxSize)
        gbs.Add(self.x, (2,1), border=0, flag=wx.EXPAND)

        label = wx.StaticText(self, wx.ID_ANY, 'y: ')
        gbs.Add(label, (2,2), border=0,
                flag=(wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT))
        self.y = wx.TextCtrl(self, value=str(self.v_y), size=OffsetBoxSize)
        gbs.Add(self.y, (2,3), border=0, flag=wx.EXPAND)

        label = wx.StaticText(self, wx.ID_ANY, 'offset_x: ')
        gbs.Add(label, (3,0), border=0,
                flag=(wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT))
        self.offset_x = wx.TextCtrl(self, value=str(self.v_offset_x),
                                    size=OffsetBoxSize)
        gbs.Add(self.offset_x, (3,1), border=0, flag=wx.EXPAND)

        label = wx.StaticText(self, wx.ID_ANY, '  offset_y: ')
        gbs.Add(label, (3,2), border=0,
                flag=(wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT))
        self.offset_y = wx.TextCtrl(self, value=str(self.v_offset_y),
                                    size=OffsetBoxSize)
        gbs.Add(self.offset_y, (3,3), border=0, flag=wx.EXPAND)

        delete_button = wx.Button(self, label='Remove')
        gbs.Add(delete_button, (4,2), border=5, flag=wx.EXPAND)
        update_button = wx.Button(self, label='Update')
        gbs.Add(update_button, (4,3), border=5, flag=wx.EXPAND)

        sbs.Add(gbs)
        self.SetSizer(sbs)
        sbs.Fit(self)

        self.filename.Bind(wx.EVT_LEFT_UP, self.onFilename)
        delete_button.Bind(wx.EVT_BUTTON, self.onDelete)
        update_button.Bind(wx.EVT_BUTTON, self.onUpdate)

    def onFilename(self, event):
        """Change image filename."""

        log('onFilename')

        wildcard = ("PNG files (*.png)|*.png|"
                    "JPG files (*.jpg)|*.jpg|"
                    "All files (*.*)|*.*")

        filepath = None

        dialog = wx.FileDialog(None, "Choose an image file",
                               os.getcwd(), "", wildcard, wx.OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            filepath = dialog.GetPath() 
        dialog.Destroy()

        if filepath:
            self.filename.SetValue(filepath)

    def onDelete(self, event):
        """Remove image from map."""

        event = LayerControlEvent(myEVT_DELETE, self.GetId())
        self.GetEventHandler().ProcessEvent(event)

    def onUpdate(self, event):
        """Update image on map."""

        event = LayerControlEvent(myEVT_UPDATE, self.GetId())

        event.filename = self.filename.GetValue()
        event.placement = self.placement.GetValue()
        event.x = self.x.GetValue()
        event.y = self.y.GetValue()
        event.offset_x = self.offset_x.GetValue()
        event.offset_y = self.offset_y.GetValue()

        self.GetEventHandler().ProcessEvent(event)

################################################################################
# The main application frame
################################################################################

class AppFrame(wx.Frame):
    def __init__(self, tile_dir=TileDirectory, levels=None):
        wx.Frame.__init__(self, None, size=DefaultAppSize,
                          title='%s, test version %s' % (DemoName, DemoVersion))
        self.SetMinSize(DefaultAppSize)
        self.panel = wx.Panel(self, wx.ID_ANY)
        self.panel.SetBackgroundColour(wx.WHITE)
        self.panel.ClearBackground()

        self.tile_directory = tile_dir
        self.tile_source = Tiles(tile_dir, levels)

        # build the GUI
        self.make_gui(self.panel)

        # set initial view position
        self.map_level.SetLabel('%d' % InitialViewLevel)
        wx.CallAfter(self.final_setup, InitialViewLevel, InitialViewPosition)

        # force pyslip initialisation
        self.pyslip.OnSize()

        # finally, set up application window position
        self.Centre()

        # initialise state variables
        self.image_layer = None
        self.image_view_layer = None

        # finally, bind pySlip events to handlers
        self.pyslip.Bind(pyslip.EVT_PYSLIP_POSITION, self.handle_position_event)
        self.pyslip.Bind(pyslip.EVT_PYSLIP_LEVEL, self.handle_level_change)

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
        all_display.Add(sl_box, proportion=1, border=0, flag=wx.EXPAND)

        # small spacer here - separate view and controls
        all_display.AddSpacer(HSpacerSize)

        # add controls to right of spacer
        controls = self.make_gui_controls(parent)
        all_display.Add(controls, proportion=0, border=0)

        parent.SetSizerAndFit(all_display)

    def make_gui_view(self, parent):
        """Build the map view widget

        parent  reference to the widget parent

        Returns the static box sizer.
        """

        # create gui objects
        sb = AppStaticBox(parent, '')
        self.pyslip = pyslip.PySlip(parent, tile_src=self.tile_source,
                                    min_level=MinTileLevel,
                                    tilesets=['./tilesets'])

        # lay out objects
        box = wx.StaticBoxSizer(sb, orient=wx.HORIZONTAL)
        box.Add(self.pyslip, proportion=1, border=0, flag=wx.EXPAND)

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

        # vertical spacer
        controls.AddSpacer(VSpacerSize)

        # controls for map-relative image layer
        self.image = self.make_gui_image(parent)
        controls.Add(self.image, proportion=0, flag=wx.EXPAND|wx.ALL)
        self.image.Bind(EVT_DELETE, self.imageDelete)
        self.image.Bind(EVT_UPDATE, self.imageUpdate)

        # vertical spacer
        controls.AddSpacer(VSpacerSize)

        # controls for image-relative image layer
        self.image_view = self.make_gui_image_view(parent)
        controls.Add(self.image_view, proportion=0, flag=wx.EXPAND|wx.ALL)
        self.image_view.Bind(EVT_DELETE, self.imageViewDelete)
        self.image_view.Bind(EVT_UPDATE, self.imageViewUpdate)

        # vertical spacer
        controls.AddSpacer(VSpacerSize)

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

    def make_gui_image(self, parent):
        """Build the image part of the controls part of GUI.

        parent  reference to parent

        Returns reference to containing sizer object.
        """

        # create widgets
        image_obj = LayerControl(parent, 'Image, map-relative',
                                 filename=DefaultFilename,
                                 placement=DefaultPlacement,
                                 x=DefaultX, y=DefaultY,
                                 offset_x=DefaultOffsetX,
                                 offset_y=DefaultOffsetY)

        return image_obj

    def make_gui_image_view(self, parent):
        """Build the view-relative image part of the controls part of GUI.

        parent  reference to parent

        Returns reference to containing sizer object.
        """

        # create widgets
        image_obj = LayerControl(parent, 'Image, view-relative',
                                 filename=DefaultViewFilename,
                                 placement=DefaultViewPlacement,
                                 x=DefaultViewX, y=DefaultViewY,
                                 offset_x=DefaultViewOffsetX,
                                 offset_y=DefaultViewOffsetY)

        return image_obj

    ######
    # event handlers
    ######

##### map-relative image layer

    def imageUpdate(self, event):
        """Display updated image."""

        if self.image_layer:
            self.pyslip.DeleteLayer(self.image_layer)

        # convert values to sanity for layer attributes
        image = event.filename

        placement = event.placement
        if placement == 'none':
            placement= ''

        x = event.x
        if not x:
            x = 0
        try:
            x = float(x)
        except ValueError:
            x = 0.0

        y = event.y
        if not y:
            y = 0
        try:
            y = float(y)
        except ValueError:
            y = 0.0

        off_x = event.offset_x
        if not off_x:
            off_x = 0
        try:
            off_x = int(off_x)
        except ValueError:
            x_off = 0

        y_off = event.offset_y
        if not y_off:
            y_off = 0
        try:
            y_off = int(y_off)
        except ValueError:
            y_off = 0

        image_data = [(x, y, image, {'placement': placement,
                                     'offset_x': off_x,
                                     'offset_y': y_off})]
        self.image_layer = \
            self.pyslip.AddImageLayer(image_data, map_rel=True,
                                      visible=True,
                                      name='<image_layer>')

    def imageDelete(self, event):
        """Delete the image map-relative layer."""

        if self.image_layer:
            self.pyslip.DeleteLayer(self.image_layer)
        self.image_layer = None

##### view-relative image layer

    def imageViewUpdate(self, event):
        """Display updated image."""

        if self.image_view_layer:
            self.pyslip.DeleteLayer(self.image_view_layer)

        # convert values to sanity for layer attributes
        image = event.filename
        placement = event.placement
        if placement == 'none':
            placement= ''

        x = event.x
        if not x:
            x = 0
        x = int(x)

        y = event.y
        if not y:
            y = 0
        y = int(y)

        off_x = event.offset_x
        if not off_x:
            off_x = 0
        off_x = int(off_x)

        y_off = event.offset_y
        if not y_off:
            y_off = 0
        y_off = int(y_off)

        # create a new image layer
        image_data = [(x, y, image, {'placement': placement,
                                     'offset_x': off_x,
                                     'offset_y': y_off})]
        self.image_view_layer = \
            self.pyslip.AddImageLayer(image_data, map_rel=False,
                                      visible=True,
                                      name='<image_layer>')

    def imageViewDelete(self, event):
        """Delete the image view-relative layer."""

        if self.image_view_layer:
            self.pyslip.DeleteLayer(self.image_view_layer)
        self.image_view_layer = None

    def final_setup(self, level, position):
        """Perform final setup.

        level     zoom level required
        position  position to be in centre of view

        We do this in a CallAfter() function for those operations that
        must not be done while the GUI is "fluid".
        """

        self.pyslip.GotoLevelAndPosition(level, position)

    ######
    # Exception handlers
    ######

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

###############################################################################

if __name__ == '__main__':
    import sys
    import getopt
    import traceback
    import tkinter_error

#vvvvvvvvvvvvvvvvvvvvv test code - can go away once __init__.py works
    DefaultTilesets = 'tilesets'
    CurrentPath = os.path.dirname(os.path.abspath(__file__))

    sys.path.append(os.path.join(CurrentPath, DefaultTilesets))

    log(str(sys.path))
#^^^^^^^^^^^^^^^^^^^^^ test code - can go away once __init__.py works

    # our own handler for uncaught exceptions
    def excepthook(type, value, tb):
        msg = '\n' + '=' * 80
        msg += '\nUncaught exception:\n'
        msg += ''.join(traceback.format_exception(type, value, tb))
        msg += '=' * 80 + '\n'
        log(msg)
        tkinter_error.tkinter_error(msg)
        sys.exit(1)

    # plug our handler into the python system
    sys.excepthook = excepthook

    # decide which tiles to use, default is GMT
    argv = sys.argv[1:]

    try:
        (opts, args) = getopt.getopt(argv, 'dht:', ['debug', 'help', 'tiles='])
    except getopt.error:
        usage()
        sys.exit(1)

    tile_source = 'GMT'
    debug = False
    for (opt, param) in opts:
        if opt in ['-h', '--help']:
            usage()
            sys.exit(0)
        elif opt in ['-d', '--debug']:
            debug = True
        elif opt in ('-t', '--tiles'):
            tile_source = param
    tile_source = tile_source.lower()

    # set up the appropriate tile source
    if tile_source == 'gmt':
        from gmt_local_tiles import GMTTiles as Tiles
        tile_dir = 'gmt_tiles'
    elif tile_source == 'osm':
        from osm_tiles import OSMTiles as Tiles
        tile_dir = 'osm_tiles'
    else:
        usage('Bad tile source: %s' % tile_source)
        sys.exit(3)


    # start wxPython app
    app = wx.App()
    app_frame = AppFrame(tile_dir=tile_dir) #, levels=[0,1,2,3,4])
    app_frame.Show()

    if debug:
        import wx.lib.inspection
        wx.lib.inspection.InspectionTool().Show()

    app.MainLoop()

