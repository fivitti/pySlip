#!/usr/bin/env python
# -*- coding= utf-8 -*-

"""
Program to test image map-relative and view-relative placement.
Select which to show and experiment with placement parameters.

Usage: test_image_placement.py [-h|--help] [(-t|--tiles) (GMT|OSM)]
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
InitiialViewPosition = (151.209444, -33.859972) # Sydney, Australia
ImitialGraphicDir = 'graphics'
InitialGraphic = os.path.join(ImitialGraphicDir, 'compass_rose.png')

# tiles info
TileDirectory = 'tiles'
MinTileLevel = 0

# the number of decimal places in a lon/lat display
LonLatPrecision = 3

# startup size of the application
DefaultAppSize = (1000, 700)

# how close click has to be before point is selected
# the value is distance squared (degrees^2)
PointSelectDelta = 0.025

# unselected point colour (rgb) and size
PointsColour = '#ff0000'
PointsSize = 3

# Selected point colour (rgb) and size
SelectColour = '#0000ff'
SelectSize = 5

# Polygon point colour (rgba) and size
PolygonColour = '#0000ff'
PolygonSize = 4

# Polygon2 point colour (rgba) and size
Polygon2Colour = '#000000'
Polygon2Size = 4

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

DefaultPlacement = 'ne'
DefaultX = 0
DefaultY = 0
DefaultXOffset = 0
DefaultYOffset = 0

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
#        if label:
#            label = '  ' + label + '  '
        if 'style' not in kwargs:
            kwargs['style'] = wx.NO_BORDER
        wx.StaticBox.__init__(self, parent, wx.ID_ANY, label, *args, **kwargs)

###############################################################################
# Class for a LayerControl widget.
#
# This is used to control each type of layer, whether map- or view-relative.
###############################################################################

myEVT_POSNCHANGE = wx.NewEventType()
myEVT_DELETE = wx.NewEventType()
myEVT_UPDATE = wx.NewEventType()

EVT_POSNCHANGE = wx.PyEventBinder(myEVT_POSNCHANGE, 1)
EVT_DELETE = wx.PyEventBinder(myEVT_DELETE, 1)
EVT_UPDATE = wx.PyEventBinder(myEVT_UPDATE, 1)

class LayerControlEvent(wx.PyCommandEvent):
    """Event sent when a LayerControl is changed."""

    def __init__(self, eventType, id):
        wx.PyCommandEvent.__init__(self, eventType, id)

class LayerControl(wx.Panel):

    def __init__(self, parent, title, filename='', placement='cc',
                 x=0, y=0, x_offset=0, y_offset=0,
                 **kwargs):
        """Initialise a LayerControl instance.

        parent      reference to parent object
        title       text to show in static box outline
        filename    filename of image to show
        placement   placement string for image
        x, y        X and Y coords
        x_offset    X offset of image
        y_offset    Y offset of image
        **kwargs    keyword args for Panel
        """

        # create and initialise the base panel
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY, **kwargs)
        self.SetBackgroundColour(wx.WHITE)

        self.v_filename = filename
        self.v_placement = placement
        self.v_x = x
        self.v_y = y
        self.v_x_offset = x_offset
        self.v_y_offset = y_offset

        box = AppStaticBox(self, title)
        sbs = wx.StaticBoxSizer(box, orient=wx.VERTICAL)
        gbs = wx.GridBagSizer(vgap=2, hgap=2)

        label = wx.StaticText(self, wx.ID_ANY, 'filename: ')
        gbs.Add(label, (0,0), border=0, flag=(wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT))
        self.filename = ROTextCtrl(self, filename, size=FilenameBoxSize)
        gbs.Add(self.filename, (0,1), span=(1,3), border=0, flag=wx.EXPAND)

        label = wx.StaticText(self, wx.ID_ANY, 'placement: ')
        gbs.Add(label, (1,0), border=0, flag=(wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT))
        choices = ['nw', 'cn', 'ne', 'ce', 'se', 'cs', 'sw', 'cw', 'cc', 'none']
        style=wx.CB_DROPDOWN|wx.CB_READONLY
        self.placement = wx.ComboBox(self, value=DefaultPlacement, size=PlacementBoxSize, choices=choices, style=style)
        gbs.Add(self.placement, (1,1), border=0)

        label = wx.StaticText(self, wx.ID_ANY, 'x: ')
        gbs.Add(label, (2,0), border=0, flag=(wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT))
        self.x = wx.TextCtrl(self, value=str(DefaultX), size=OffsetBoxSize)
        gbs.Add(self.x, (2,1), border=0, flag=wx.EXPAND)

        label = wx.StaticText(self, wx.ID_ANY, 'y: ')
        gbs.Add(label, (2,2), border=0, flag=(wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT))
        self.y = wx.TextCtrl(self, value=str(DefaultY), size=OffsetBoxSize)
        gbs.Add(self.y, (2,3), border=0, flag=wx.EXPAND)

        label = wx.StaticText(self, wx.ID_ANY, 'x_offset: ')
        gbs.Add(label, (3,0), border=0, flag=(wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT))
        self.x_offset = wx.TextCtrl(self, value=str(DefaultXOffset), size=OffsetBoxSize)
        gbs.Add(self.x_offset, (3,1), border=0, flag=wx.EXPAND)

        label = wx.StaticText(self, wx.ID_ANY, '  y_offset: ')
        gbs.Add(label, (3,2), border=0, flag=(wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT))
        self.y_offset = wx.TextCtrl(self, value=str(DefaultYOffset), size=OffsetBoxSize)
        gbs.Add(self.y_offset, (3,3), border=0, flag=wx.EXPAND)

        delete_button = wx.Button(self, label='Remove')
        gbs.Add(delete_button, (4,2), border=5, flag=wx.EXPAND)
        update_button = wx.Button(self, label='Update')
        gbs.Add(update_button, (4,3), border=5, flag=wx.EXPAND)

        sbs.Add(gbs)
        self.SetSizer(sbs)
        sbs.Fit(self)

        # tie handlers to change events
#        self.filename.Bind(wx.EVT_LEFT_UP, self.onFilenameChange)
#        self.placement.Bind(wx.EVT_COMBOBOX, self.onPlacementChange)
#        self.x.Bind(wx.EVT_TEXT, self.onPositionChange)
#        self.y.Bind(wx.EVT_TEXT, self.onPositionChange)
#        self.x_offset.Bind(wx.EVT_TEXT, self.onOffsetChange)
#        self.y_offset.Bind(wx.EVT_TEXT, self.onOffsetChange)

        delete_button.Bind(wx.EVT_BUTTON, self.onDelete)
        update_button.Bind(wx.EVT_BUTTON, self.onUpdate)

#    def onFilenameChange(self, event):
#        """Image filename changed."""
#        log('onFilenameChange')
#        event = LayerControlEvent(myEVT_POSNCHANGE, self.GetId())
#        self.GetEventHandler().ProcessEvent(event)
#
#    def onPlacementChange(self, event):
#        log('onPlacementChange')
#        event = LayerControlEvent(myEVT_POSNCHANGE, self.GetId())
#        self.GetEventHandler().ProcessEvent(event)
#
#    def onPositionChange(self, event):
#        log('onPositionChange')
#        event = LayerControlEvent(myEVT_POSNCHANGE, self.GetId())
#        self.GetEventHandler().ProcessEvent(event)
#
#    def onOffsetChange(self, event):
#        log('onPositionChange')
#        event = LayerControlEvent(myEVT_POSNCHANGE, self.GetId())
#        self.GetEventHandler().ProcessEvent(event)

#    def onChange(self, event):
#        """Image position or picture changed."""
#
#        log('onChange')
#        event = LayerControlEvent(myEVT_POSNCHANGE, self.GetId())
#        self.GetEventHandler().ProcessEvent(event)

    def onDelete(self, event):
        """Remove image from map."""
        log('onDelete')
        event = LayerControlEvent(myEVT_DELETE, self.GetId())
        self.GetEventHandler().ProcessEvent(event)

    def onUpdate(self, event):
        """Update image on map."""

        log('onUpdate')

        event = LayerControlEvent(myEVT_UPDATE, self.GetId())

        event.filename = self.filename.GetValue()
        event.placement = self.placement.GetValue()
        event.x = self.x.GetValue()
        event.y = self.y.GetValue()
        event.x_offset = self.x_offset.GetValue()
        event.y_offset = self.y_offset.GetValue()

        self.GetEventHandler().ProcessEvent(event)

###############################################################################
# The main application frame
###############################################################################

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

        # do initialisation stuff - all the application stuff
        self.init()

        # finally, set up application window position
        self.Centre()

        # create select event dispatch directory
        self.demo_select_dispatch = {}

        # initialise state variables
        self.image_layer = None
        self.image_view_layer = None

        # finally, bind events to handlers
        self.pyslip.Bind(pyslip.EVT_PYSLIP_POSITION,
                         self.handle_position_event)
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
        sb = AppStaticBox(parent, '', style=wx.NO_BORDER)
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
                                 filename='', placement='',
                                 x=0, y=0, x_offset=0, y_offset=0)

        return image_obj

    def make_gui_image_view(self, parent):
        """Build the view-relative image part of the controls part of GUI.

        parent  reference to parent

        Returns reference to containing sizer object.
        """

        # create widgets
        image_obj = LayerControl(parent, 'Image, view-relative',
                                 filename='', placement='',
                                 x=0, y=0, x_offset=0, y_offset=0)

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
        image = ShipImg
        placement = event.placement
        if placement == 'none':
            placement= ''
        x = event.x
        if not x:
            x = 0
        y = event.y
        if not y:
            y = 0
        x_offset = event.x_offset
        if not x_offset:
            x_offset = 0
        y_offset = event.y_offset
        if not y_offset:
            y_offset = 0

        image_data = [(x, y, image, {'placement': placement,
                                     'x_offset': x_offset,
                                     'y_offset': y_offset})]
        self.image_layer = \
            self.pyslip.AddImageLayer(image_data, map_rel=True,
                                      visible=True,
                                      name='<image_layer>')

    def imageDelete(self, event):
        log('imageDelete')

        if self.image_layer:
            self.pyslip.DeleteLayer(self.image_layer)
        self.image_layer = None

    def imageOnOff(self, event):
        """Handle OnOff event for map-relative image layer control."""

        if event.state:
            self.image_layer = \
                self.pyslip.AddImageLayer(ImageData, map_rel=True,
                                          visible=True,
                                          name='<image_layer>')
        else:
            self.pyslip.DeleteLayer(self.image_layer)
            self.image_layer = None
            if self.sel_image_layer:
                self.pyslip.DeleteLayer(self.sel_image_layer)
                self.sel_image_layer = None
                self.sel_image = None

    def imageShowOnOff(self, event):
        """Handle ShowOnOff event for image layer control."""

        if event.state:
            self.pyslip.ShowLayer(self.image_layer)
            if self.sel_image_layer:
                self.pyslip.ShowLayer(self.sel_image_layer)
        else:
            self.pyslip.HideLayer(self.image_layer)
            if self.sel_image_layer:
                self.pyslip.HideLayer(self.sel_image_layer)

    def imageSelectOnOff(self, event):
        """Handle SelectOnOff event for image layer control."""

        layer = self.image_layer
        if event.state:
            self.add_select_handler(layer, self.imageSelect)
            self.pyslip.SetLayerSelectable(layer, True)
        else:
            self.del_select_handler(layer)
            self.pyslip.SetLayerSelectable(layer, False)

    def imageSelect(self, event):
        """Select event from pyslip."""

        point = event.point

        if event.evtype == pyslip.EventPointSelect:
            if point == self.sel_image:
                # select again, turn point off
                self.sel_image = None
                self.pyslip.DeleteLayer(self.sel_image_layer)
                self.sel_image_layer = None
            elif point:
                if self.sel_image_layer:
                    self.pyslip.DeleteLayer(self.sel_image_layer)
                self.sel_image = point
                self.sel_image_layer = \
                    self.pyslip.AddPointLayer((point,), map_rel=True,
                                              color='#0000ff',
                                              radius=5, visible=True,
                                              show_levels=[3,4],
                                              name='<sel_pt_layer>')
        elif event.evtype == pyslip.EventBoxSelect:
            # remove any previous selection
            if self.sel_image_layer:
                self.pyslip.DeleteLayer(self.sel_image_layer)
                self.sel_image_layer = None

            if point:
                self.sel_image_layer = \
                    self.pyslip.AddPointLayer(point, map_rel=True,
                                              color='#00ffff',
                                              radius=5, visible=True,
                                              show_levels=[3,4],
                                              name='<boxsel_pt_layer>')
                self.pyslip.PlaceLayerBelowLayer(self.sel_image_layer,
                                                 self.image_layer)

        return True

    def imageBSelect(self, id, points=None):
        """Select event from pyslip."""

        # remove any previous selection
        if self.sel_image_layer:
            self.pyslip.DeleteLayer(self.sel_image_layer)
            self.sel_image_layer = None

        if points:
            self.sel_image_layer = \
                self.pyslip.AddPointLayer(points, map_rel=True,
                                          color='#e0e0e0',
                                          radius=13, visible=True,
                                          show_levels=[3,4],
                                          name='<boxsel_img_layer>')
            self.pyslip.PlaceLayerBelowLayer(self.sel_image_layer,
                                             self.image_layer)

        return True

##### view-relative image layer

    def imageViewUpdate(self, event):
        """Display updated image."""

        if self.image_view_layer:
            self.pyslip.DeleteLayer(self.image_view_layer)

        # convert values to sanity for layer attributes
        image = CompassRoseGraphic
        placement = event.placement
        if placement == 'none':
            placement= ''
        x = event.x
        if not x:
            x = 0
        y = event.y
        if not y:
            y = 0
        x_offset = event.x_offset
        if not x_offset:
            x_offset = 0
        y_offset = event.y_offset
        if not y_offset:
            y_offset = 0

        image_data = [(x, y, image, {'placement': placement,
                                     'x_offset': x_offset,
                                     'y_offset': y_offset})]
        self.image_view_layer = \
            self.pyslip.AddImageLayer(image_data, map_rel=False,
                                      visible=True,
                                      name='<image_layer>')

    def imageViewDelete(self, event):
        log('imageViewDelete')

        if self.image_view_layer:
            self.pyslip.DeleteLayer(self.image_view_layer)
        self.image_view_layer = None

    def imageViewOnOff(self, event):
        """Handle OnOff event for view-relative image layer control."""

        if event.state:
            self.image_view_layer = \
                self.pyslip.AddImageLayer(ImageViewData, map_rel=False,
                                          visible=True,
                                          name='<image_view_layer>')
        else:
            self.pyslip.DeleteLayer(self.image_view_layer)
            self.image_view_layer = None
            if self.sel_image_view_layer:
                self.pyslip.DeleteLayer(self.sel_image_view_layer)
                self.sel_image_view_layer = None
                self.sel_image_view_point = None

    def imageViewShowOnOff(self, event):
        """Handle ShowOnOff event for image layer control."""

        if event.state:
            self.pyslip.ShowLayer(self.image_view_layer)
            if self.sel_image_view_layer:
                self.pyslip.ShowLayer(self.sel_image_layer)
        else:
            self.pyslip.HideLayer(self.image_view_layer)
            if self.sel_image_view_layer:
                self.pyslip.HideLayer(self.sel_image_layer)

    def imageViewSelectOnOff(self, event):
        """Handle SelectOnOff event for image layer control."""

        layer = self.image_view_layer
        if event.state:
            self.add_select_handler(layer, self.imageViewSelect)
            self.pyslip.SetLayerSelectable(layer, True)
        else:
            self.del_select_handler(layer)
            self.pyslip.SetLayerSelectable(layer, False)

    def imageViewSelect(self, event):
        """View-relative image select event from pyslip.

        event  the wxpython event object

        The 'event' object has attributes:
        evtype    the pySlip event type
        layer_id  'id' of the layer in which the image selected exists
        mposn     the geo coords of the click
        point     point datas is a list of: (pt, udata)
                    pt is an (x,y) tuple of relative click posn within the image
                    udata is userdata attached to the image (if any).
        vposn     the view coords of the click

        The code below doesn't assume a placement of the selected image, it
        figures out the correct position of the 'highlight' layers.  This helps
        with debugging, as we can move the compass rose anywhere we like.
        """

        log('imageViewSelect: event=%s' % str(event))

        log('imageViewSelect: event.evtype=%s' % str(event.evtype))
        log('imageViewSelect: event.layer_id=%s' % str(event.layer_id))
        log('imageViewSelect: event.mposn=%s' % str(event.mposn))
        log('imageViewSelect: event.point=%s' % str(event.point))
        log('imageViewSelect: event.vposn=%s' % str(event.vposn))

        # only one image selectable, remove old selection (if any)
        if self.sel_image_view_layer:
            # already selected, remove old selection
            self.pyslip.DeleteLayer(self.sel_image_view_layer)
            self.sel_image_view_layer = None
            self.pyslip.DeleteLayer(self.sel_imagepoint_view_layer)
            self.sel_imagepoint_view_layer = None

        if event.point:
            # unpack event data
            (pp, udata) = event.point[0]
            (sel_x, sel_y) = pp     # select relative point in image

            # figure out compass rose attributes
            attr_dict = ImageViewData[0][3]
            img_placement = attr_dict['placement']

            # add selection point
            point_place_coords = {'ne': '(sel_x - CR_Width, sel_y)',
                                  'ce': '(sel_x - CR_Width, sel_y - CR_Height/2.0)',
                                  'se': '(sel_x - CR_Width, sel_y - CR_Height)',
                                  'cs': '(sel_x - CR_Width/2.0, sel_y - CR_Height)',
                                  'sw': '(sel_x, sel_y - CR_Height)',
                                  'cw': '(sel_x, sel_y - CR_Height/2.0)',
                                  'nw': '(sel_x, sel_y)',
                                  'cn': '(sel_x - CR_Width/2.0, sel_y)',
                                  'cc': '(sel_x - CR_Width/2.0, sel_y - CR_Height/2.0)',
                                  '':   '(sel_x, sel_y)',
                                  None: '(sel_x, sel_y)',
                                 }

            point = eval(point_place_coords[img_placement])
            log('AddPointLayer((point,)=%s' % str(point))
            self.sel_imagepoint_view_layer = \
                self.pyslip.AddPointLayer((point,), map_rel=False,
                                          color='green',
                                          radius=5, visible=True,
                                          placement=img_placement,
                                          name='<sel_image_view_point>')

            # add polygon outline around image
            (x, y) = event.vposn
            p_dict = {'placement': img_placement, 'width': 3, 'color': 'green', 'closed': True}
            poly_place_coords = {'ne': '(((-CR_Width,0),(0,0),(0,CR_Height),(-CR_Width,CR_Height)),p_dict)',
                                 'ce': '(((-CR_Width,-CR_Height/2.0),(0,-CR_Height/2.0),(0,CR_Height/2.0),(-CR_Width,CR_Height/2.0)),p_dict)',
                                 'se': '(((-CR_Width,-CR_Height),(0,-CR_Height),(0,0),(-CR_Width,0)),p_dict)',
                                 'cs': '(((-CR_Width/2.0,-CR_Height),(CR_Width/2.0,-CR_Height),(CR_Width/2.0,0),(-CR_Width/2.0,0)),p_dict)',
                                 'sw': '(((0,-CR_Height),(CR_Width,-CR_Height),(CR_Width,0),(0,0)),p_dict)',
                                 'cw': '(((0,-CR_Height/2.0),(CR_Width,-CR_Height/2.0),(CR_Width,CR_Height/2.0),(0,CR_Height/2.0)),p_dict)',
                                 'nw': '(((0,0),(CR_Width,0),(CR_Width,CR_Height),(0,CR_Height)),p_dict)',
                                 'cn': '(((-CR_Width/2.0,0),(CR_Width/2.0,0),(CR_Width/2.0,CR_Height),(-CR_Width/2.0,CR_Height)),p_dict)',
                                 'cc': '(((-CR_Width/2.0,-CR_Height/2.0),(CR_Width/2.0,-CR_Height/2.0),(CR_Width/2.0,CR_Height/2.0),(-CR_Width/2.0,CR_Height/2.0)),p_dict)',
                                 '':   '(((x, y),(x+CR_Width,y),(x+CR_Width,y+CR_Height),(x,y+CR_Height)),p_dict)',
                                 None: '(((x, y),(x+CR_Width,y),(x+CR_Width,y+CR_Height),(x,y+CR_Height)),p_dict)',
                                }
            pdata = eval(poly_place_coords[img_placement])
            log('pdata=%s' % str(pdata))
            self.sel_image_view_layer = \
                self.pyslip.AddPolygonLayer((pdata,), map_rel=False,
#                                            placement=img_placement,
#                                            color='green',
#                                            width=5, visible=True,
                                            name='<sel_image_view_outline>',
                                           )

        return True

    ######
    # Finish initialization of data, etc
    ######

    def init(self):
        global PointData, PointDataColour
        global PointViewData, PointViewDataColour
        global ImageData
        global ImageViewData
        global TextData # , TextDataColour
        global TextViewData
        global PolyData
        global PolyViewData
        global CR_Width, CR_Height

        # create PointData
        PointData = []
        count = 0
        for lon in range(-70, 290+1, 5):
            for lat in range(-65, 65+1, 5):
                PointData.append((lon, lat, {'data': count}))
                count += 1
        PointDataColour = '#ff000080'	# semi-transparent

        # create PointViewData - a point-rendition of 'PYSLIP'
        PointViewData = [(-66,-14),(-66,-13),(-66,-12),(-66,-11),(-66,-10),
                         (-66,-9),(-66,-8),(-66,-7),(-66,-6),(-66,-5),(-66,-4),
                         (-66,-3),(-65,-7),(-64,-7),(-63,-7),(-62,-7),(-61,-8),
                         (-60,-9),(-60,-10),(-60,-11),(-60,-12),(-61,-13),
                         (-62,-14),(-63,-14),(-64,-14),(65,-14),            # P
                         (-59,-14),(-58,-13),(-57,-12),(-56,-11),(-55,-10),
                         (-53,-10),(-52,-11),(-51,-12),(-50,-13),(-49,-14),
                         (-54,-9),(-54,-8),(-54,-7),(-54,-6),(-54,-5),
                         (-54,-4),(-54,-3),                                 # Y
                         (-41,-13),(-42,-14),(-43,-14),(-44,-14),(-45,-14),
                         (-46,-14),(-47,-13),(-48,-12),(-48,-11),(-47,-10),
                         (-46,-9),(-45,-9),(-44,-9),(-43,-9),(-42,-8),
                         (-41,-7),(-41,-6),(-41,-5),(-42,-4),(-43,-3),
                         (-44,-3),(-45,-3),(-46,-3),(-47,-3),(-48,-4),      # S
                         (-39,-14),(-39,-13),(-39,-12),(-39,-11),(-39,-10),
                         (-39,-9),(-39,-8),(-39,-7),(-39,-6),(-39,-5),
                         (-39,-4),(-39,-3),(-38,-3),(-37,-3),(-36,-3),
                         (-35,-3),(-34,-3),(-33,-3),(-32,-3),               # L
                         (-29,-14),(-29,-13),(-29,-12),
                         (-29,-11),(-29,-10),(-29,-9),(-29,-8),(-29,-7),
                         (-29,-6),(-29,-5),(-29,-4),(-29,-3),               # I
                         (-26,-14),(-26,-13),(-26,-12),(-26,-11),(-26,-10),
                         (-26,-9),(-26,-8),(-26,-7),(-26,-6),(-26,-5),(-26,-4),
                         (-26,-3),(-25,-7),(-24,-7),(-23,-7),(-22,-7),(-21,-8),
                         (-20,-9),(-20,-10),(-20,-11),(-20,-12),(-21,-13),
                         (-22,-14),(-23,-14),(-24,-14),(25,-14)]            # P
        PointViewDataColour = '#00ff0020'	# very transparent

        # create image data
        ImageData = [# Agnes Napier - 1855
                     (160.0, -30.0, ShipImg, {'placement': 'cc'}),
                     # Venus - 1826
                     (145.0, -11.0, ShipImg, {'placement': 'ne'}),
                     # Wolverine - 1879
                     (156.0, -23.0, ShipImg, {'placement': 'nw'}),
                     # Thomas Day - 1884
                     (150.0, -15.0, ShipImg, {'placement': 'sw'}),
                     # Sybil - 1902
                     (165.0, -19.0, ShipImg, {'placement': 'se'}),
                     # Prince of Denmark - 1863
                     (158.55, -19.98, ShipImg),
                     # Moltke - 1911
                     (146.867525, -19.152185, ShipImg)
                    ]
        ImageData2 = []
        ImageData3 = []
        ImageData4 = []
        ImageData5 = []
        ImageData6 = []
        self.map_level_2_img = {0: ImageData2,
                                1: ImageData3,
                                2: ImageData4,
                                3: ImageData5,
                                4: ImageData6}
        self.map_level_2_selimg = {0: SelGlassyImg2,
                                   1: SelGlassyImg3,
                                   2: SelGlassyImg4,
                                   3: SelGlassyImg5,
                                   4: SelGlassyImg6}
        self.current_layer_img_layer = None
        for x in range(80):
            for y in range(40):
                ImageData.append((-30+x*2, y*2-30, GlassyImg4))

        ImageViewData = [(0, 0, CompassRoseGraphic, {'placement': 'cc',
                                                     'data': 'compass rose'})]

        text_placement = {'placement': 'se'}
        transparent_placement = {'placement': 'se', 'colour': '#00000040'}
        capital = {'placement': 'se', 'fontsize': 14, 'color': 'red',
                   'textcolour': 'red'}
        TextData = [(151.20, -33.85, 'Sydney', text_placement),
                    (144.95, -37.84, 'Melbourne', {'placement': 'ce'}),
                    (153.08, -27.48, 'Brisbane', text_placement),
                    (115.86, -31.96, 'Perth', transparent_placement),
                    (138.30, -35.52, 'Adelaide', text_placement),
                    (130.98, -12.61, 'Darwin', text_placement),
                    (147.31, -42.96, 'Hobart', text_placement),
                    (174.75, -36.80, 'Auckland', text_placement),
                    (174.75, -41.29, 'Wellington', capital),
                    (172.61, -43.51, 'Christchurch', text_placement),
                    (168.74, -45.01, 'Queenstown', text_placement),
                    (147.30, -09.41, 'Port Moresby', capital),
                    (106.822922, -6.185451, 'Jakarta', capital),
                    (110.364444, -7.801389, 'Yogyakarta', text_placement),
                    (120.966667, 14.563333, 'Manila', capital),
                    (271.74, +40.11, 'Champaign', text_placement),
                    (160.0, -30.0, 'Agnes Napier - 1855',
                        {'placement': 'cw', 'offset_x': 20, 'color': 'green'}),
                    (145.0, -11.0, 'Venus - 1826',
                        {'placement': 'sw', 'color': 'green'}),
                    (156.0, -23.0, 'Wolverine - 1879',
                        {'placement': 'ce', 'color': 'green'}),
                    (150.0, -15.0, 'Thomas Day - 1884',
                        {'color': 'green'}),
                    (165.0, -19.0, 'Sybil - 1902',
                        {'placement': 'cw', 'color': 'green'}),
                    (158.55, -19.98, 'Prince of Denmark - 1863',
                        {'placement': 'nw', 'offset_x': 20, 'color': 'green'}),
                    (146.867525, -19.152182, 'Moltke - 1911',
                        {'placement': 'ce', 'offset_x': 20, 'color': 'green'})
                   ]
        if sys.platform != 'win32':
            TextData.extend([
                    (106.36, +10.36, 'Mỹ Tho', {'placement': 'ne'}),
                    (105.85, +21.033333, 'Hà Nội', capital),
                    (106.681944, 10.769444, 'Thành phố Hồ Chí Minh',
                        {'placement': 'sw'}),
                    (132.47, +34.44, '広島市 (Hiroshima City)',
                        text_placement),
                    (114.158889, +22.278333, '香港 (Hong Kong)',
                        {'placement': 'nw'}),
                    ( 96.16, +16.80, 'ရန်ကုန် (Yangon)', capital),
                    (104.93, +11.54, ' ភ្នំពេញ (Phnom Penh)',
                        {'placement': 'ce', 'fontsize': 12, 'color': 'red'}),
                    (100.49, +13.75, 'กรุงเทพมหานคร (Bangkok)', capital),
                    ( 77.56, +34.09, 'གླེ་(Leh)', text_placement),
                    (84.991275, 24.695102, 'बोधगया (Bodh Gaya)', text_placement)])
#        TextDataColour = '#ffffff40'

        TextViewData = [(0, 7, '%s %s' % (DemoName, DemoVersion))]

        PolyData = [(((150,10),(160,20),(170,10),(165,0),(155,0)),
                      {'width': 3, 'color': 'blue', 'closed': True}),
                    (((165,-35),(175,-35),(175,-45),(165,-45)),
                      {'width': 10, 'color': '#00ff00c0', 'filled': True,
                       'fillcolor': '#ffff0040'}),
                    (((190,-30),(220,-50),(220,-30),(190,-50)),
                      {'width': 3, 'color': 'green', 'filled': True,
                       'fillcolor': 'yellow'}),
                    (((190,+50),(220,+65),(220,+50),(190,+65)),
                      {'width': 10, 'color': '#00000040'})
                   ]

        PolyViewData = [(((0,0),(230,0),(230,40),(-230,40),(-230,0)),
                        {'width': 3, 'color': '#00ff00ff', 'closed': True,
                         'placement': 'cn', 'offset_y': 1})]

        # define layer ID variables & sub-checkbox state variables
        self.point_layer = None
        self.sel_point_layer = None
        self.sel_point = None

        self.point_view_layer = None
        self.sel_point_view_layer = None
        self.sel_point_view = None

        self.image_layer = None
        self.sel_image_layer = None
        self.sel_image = None

        self.image_view_layer = None
        self.sel_image_view_layer = None
        self.sel_image_view = None
        self.sel_imagepoint_view_layer = None

        self.text_layer = None
        self.sel_text_layer = None
        self.sel_text = None

        self.text_view_layer = None
        self.sel_text_view_layer = None
        self.sel_view_text = None

        self.poly_layer = None
        self.sel_poly_layer = None
        self.sel_poly = None

        self.poly_view_layer = None
        self.sel_poly_view_layer = None
        self.sel_poly = None

        # get width and height of the compass rose image
        cr_img = wx.Image(CompassRoseGraphic, wx.BITMAP_TYPE_ANY)
        log('cr_img: %s' % str(cr_img))
        log(str(dir(cr_img)))
        cr_bmap = cr_img.ConvertToBitmap()
        (CR_Width, CR_Height) = cr_bmap.GetSize()

        # force pyslip initialisation
        self.pyslip.OnSize()

        # set initial view position
        self.map_level.SetLabel('%d' % InitialViewLevel)
        wx.CallAfter(self.final_setup, InitialViewLevel, InitiialViewPosition)

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

    def handle_select_event(self, event):
        """Handle a pySlip point/box SELECT event."""

        layer_id = event.layer_id

        self.demo_select_dispatch.get(layer_id, self.null_handler)(event)

    def null_handler(self, event):
        """Routine to handle unexpected events."""

        print('ERROR: null_handler!?')

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

    ######
    # Handle adding/removing select handler functions.
    ######

    def add_select_handler(self, id, handler):
        """Add handler for select in layer 'id'."""

        self.demo_select_dispatch[id] = handler

    def del_select_handler(self, id):
        """Remove handler for select in layer 'id'."""

        del self.demo_select_dispatch[id]

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
        (opts, args) = getopt.getopt(argv, 'ht:', ['help', 'tiles='])
    except getopt.error:
        usage()
        sys.exit(1)

    tile_source = 'GMT'
    for (opt, param) in opts:
        if opt in ['-h', '--help']:
            usage()
            sys.exit(0)
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

##    import wx.lib.inspection
##    wx.lib.inspection.InspectionTool().Show()

    app.MainLoop()

