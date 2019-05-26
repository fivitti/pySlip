"""
pySlipQt demonstration program with user-selectable tiles.

Usage: pyslipqt_demo.py <options>

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
"""


import os
import sys
import copy
import getopt
import traceback
from functools import partial

try:
    from PyQt5.QtCore import QTimer
    from PyQt5.QtGui import QPixmap
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget,
                                 QAction, QGridLayout, QErrorMessage)
except ImportError:
    msg = '*'*60 + '\nSorry, you must install PyQt5\n' + '*'*60
    print(msg)
    sys.exit(1)

try:
    import pySlipQt.pySlipQt as pySlipQt
    import pySlipQt.gmt_local as tiles
    import pySlipQt.log as log
except ImportError:
    msg = '*'*60 + '\nSorry, you must install pySlipQt\n' + '*'*60
    print(msg)
    sys.exit(1)

# initialize the logging system
try:
    log = log.Log('pyslip.log')
except AttributeError:
    # already have a log file, ignore
    pass

# get the bits of the demo program we need
from display_text import DisplayText
from layer_control import LayerControl
from appstaticbox import AppStaticBox
from rotextctrl import ROTextCtrl


######
# Various demo constants
######

# demo name/version
DemoName = 'pySlipQt %s - Demonstration' % pySlipQt.__version__
DemoVersion = '1.1'

DemoWidth = 1000
DemoHeight = 800

# initial view level and position
InitViewLevel = 4

# this will eventually be selectable within the app
# a selection of cities, position from WikiPedia, etc
InitViewPosition = (0.0, 0.0)                # "Null" Island
#InitViewPosition = (0.0, 51.48)             # Greenwich, England
#InitViewPosition = (5.33, 60.389444)        # Bergen, Norway
#InitViewPosition = (153.033333, -27.466667) # Brisbane, Australia
#InitViewPosition = (98.3786761, 7.8627326)  # Phuket (ภูเก็ต), Thailand
#InitViewPosition = (151.209444, -33.859972) # Sydney, Australia
#InitViewPosition = (-77.036667, 38.895111)  # Washington, DC, USA
#InitViewPosition = (132.455278, 34.385278)  # Hiroshima, Japan
#InitViewPosition = (-8.008889, 31.63)       # Marrakech (مراكش), Morocco
#InitViewPosition = (18.95, 69.65)           # Tromsø, Norway
#InitViewPosition = (-70.933333, -53.166667) # Punta Arenas, Chile
#InitViewPosition = (168.3475, -46.413056)   # Invercargill, New Zealand
#InitViewPosition = (-147.723056, 64.843611) # Fairbanks, AK, USA
#InitViewPosition = (103.851959, 1.290270)   # Singapore

# levels on which various layers show
MRPointShowLevels = [3, 4]
MRImageShowLevels = [3, 4]
MRTextShowLevels = [3, 4]
MRPolyShowLevels = [3, 4]
MRPolylineShowLevels = [3, 4]

# the number of decimal places in a lon/lat display
LonLatPrecision = 3

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

# list of modules containing tile sources
# list of (<long_name>, <module_name>)
# the <long_name>s go into the Tileselect menu
Tilesets = [
            ('BlueMarble tiles', 'blue_marble'),
            ('GMT tiles', 'gmt_local'),
#            ('ModestMaps tiles', 'modest_maps'),  # can't access?
#            ('MapQuest tiles', 'mapquest'),    # can't access?
            ('OpenStreetMap tiles', 'open_street_map'),
            ('Stamen Toner tiles', 'stamen_toner'),
            ('Stamen Transport tiles', 'stamen_transport'),
            ('Stamen Watercolor tiles', 'stamen_watercolor'),
           ]

# index into Tilesets above to set default tileset: GMT tiles
DefaultTilesetIndex = 1


###############################################################################
# A small class to manage tileset sources.
###############################################################################

class TilesetManager:
    """A class to manage multiple tileset objects.
  
        ts = TilesetManager(source_list)  # 'source_list' is list of tileset source modules
        ts.get_tile_source(index)         # 'index' into 'source_list' of source to use

    Features 'lazy' importing, only imports when the tileset is used
    the first time.
    """

    def __init__(self, mod_list):
        """Create a set of tile sources.
        
        mod_list  list of module filenames to manage

        The list is something like: ['osm_tiles.py', 'gmt_local.py']

        We can access tilesets using the index of the module in the 'mod_list'.
        """

        self.modules = []
        for fname in mod_list:
            self.modules.append([fname, os.path.splitext(fname)[0], None])

    def get_tile_source(self, mod_index):
        """Get an open tileset source for given name.

        mod_index  index into self.modules of tileset to use
        """

        tileset_data = self.modules[mod_index]
        (filename, modulename, tile_obj) = tileset_data
        if not tile_obj:
            # have never used this tileset, import and instantiate
            obj = __import__('pySlipQt', globals(), locals(), [modulename])
            tileset = getattr(obj, modulename)
            tile_obj = tileset.Tiles()
            tileset_data[2] = tile_obj
        return tile_obj

###############################################################################
# The main application frame
###############################################################################

class PySlipQtDemo(QMainWindow):
    def __init__(self):
        super().__init__()

        # initialize the tileset handler
        self.tileset_manager = self.init_tiles()
        self.tile_source = self.tileset_manager.get_tile_source(DefaultTilesetIndex)

        # start the GUI
        grid = QGridLayout()
        grid.setColumnStretch(0, 1)
        grid.setContentsMargins(2, 2, 2, 2)

        qwidget = QWidget(self)
        qwidget.setLayout(grid)
        self.setCentralWidget(qwidget)

        # build the 'controls' part of GUI
        num_rows = self.make_gui_controls(grid)

        self.pyslip = pySlipQt.PySlipQt(self, tile_src=self.tile_source,
                                        start_level=InitViewLevel)
        grid.addWidget(self.pyslip, 0, 0, num_rows+1, 1)
        grid.setRowStretch(num_rows, 1)

        # add the menus
        self.initMenu()

        # do initialisation stuff - all the application stuff
        self.initData()

        # create select event dispatch directory
        self.demo_select_dispatch = {}

        # selected point, if not None
        self.point_layer = None

        # variables referencing various layers
        self.sel_text_highlight = None

        # bind events to handlers
        self.pyslip.events.EVT_PYSLIPQT_LEVEL.connect(self.level_change_event)
        self.pyslip.events.EVT_PYSLIPQT_POSITION.connect(self.mouse_posn_event)
        self.pyslip.events.EVT_PYSLIPQT_SELECT.connect(self.select_event)
        self.pyslip.events.EVT_PYSLIPQT_BOXSELECT.connect(self.select_event)

        # set the size of the demo window, etc
        self.setGeometry(300, 300, DemoWidth, DemoHeight)
        self.setWindowTitle('%s %s' % (DemoName, DemoVersion))
        self.show()

        # set initial view position
        self.pyslip.GotoLevelAndPosition(InitViewLevel, InitViewPosition)

#####
# Build the GUI
#####

    def make_gui_controls(self, grid):
        """Build the 'controls' part of the GUI

        grid  reference to grid that we populate

        Returns the number of rows add ed to the 'grid' layout.
        """

        # the 'grid_row' variable is row to add into
        grid_row = 0

        # put level and position into grid at top right
        self.map_level = DisplayText(title='', label='Level:',
                                     tooltip=None)
        grid.addWidget(self.map_level, grid_row, 1, 1, 1)
        self.mouse_position = DisplayText(title='',
                                          label='Lon/Lat:', text_width=100,
                                          tooltip='Shows the mouse longitude and latitude on the map',)
        grid.addWidget(self.mouse_position, grid_row, 2, 1, 1)
        grid_row += 1

        # controls for map-relative points layer
        self.lc_point = LayerControl(self, title='Points, map relative %s'
                                     % (str(MRPointShowLevels) if MRPointShowLevels else ''),
                                     selectable=True)
        self.lc_point.change_add.connect(self.pointOnOff)   # tie to event handler(s)
        self.lc_point.change_show.connect(self.pointShowOnOff)
        self.lc_point.change_select.connect(self.pointSelectOnOff)
        grid.addWidget(self.lc_point, grid_row, 1, 1, 2)
        grid_row += 1

        # controls for view-relative points layer
        self.lc_point_v = LayerControl(self, 'Points, view relative', selectable=True)
        self.lc_point_v.change_add.connect(self.pointViewOnOff)   # tie to event handler(s)
        self.lc_point_v.change_show.connect(self.pointViewShowOnOff)
        self.lc_point_v.change_select.connect(self.pointViewSelectOnOff)
        grid.addWidget(self.lc_point_v, grid_row, 1, 1, 2)
        grid_row += 1

        # controls for map-relative image layer
        self.lc_image = LayerControl(self, 'Images, map relative %s'
                                     % (str(MRImageShowLevels) if MRImageShowLevels else ''),
                                        selectable=True)
        self.lc_image.change_add.connect(self.imageOnOff)   # tie to event handler(s)
        self.lc_image.change_show.connect(self.imageShowOnOff)
        self.lc_image.change_select.connect(self.imageSelectOnOff)
        grid.addWidget(self.lc_image, grid_row, 1, 1, 2)
        grid_row += 1

        # controls for map-relative image layer
        self.lc_image_v = LayerControl(self, 'Images, view relative', selectable=True) 
        self.lc_image_v.change_add.connect(self.imageViewOnOff)   # tie to event handler(s)
        self.lc_image_v.change_show.connect(self.imageViewShowOnOff)
        self.lc_image_v.change_select.connect(self.imageViewSelectOnOff)
        grid.addWidget(self.lc_image_v, grid_row, 1, 1, 2)
        grid_row += 1

        # controls for map-relative text layer
        self.lc_text = LayerControl(self, 'Text, map relative %s'
                                    % (str(MRTextShowLevels) if MRTextShowLevels else ''),
                                    selectable=True)
        self.lc_text.change_add.connect(self.textOnOff)     # tie to event handler(s)
        self.lc_text.change_show.connect(self.textShowOnOff)
        self.lc_text.change_select.connect(self.textSelectOnOff)
        grid.addWidget(self.lc_text, grid_row, 1, 1, 2)
        grid_row += 1

        # controls for view-relative text layer
        self.lc_text_v = LayerControl(self, 'Text, view relative', selectable=True)
        self.lc_text_v.change_add.connect(self.textViewOnOff)    # tie to event handler(s)
        self.lc_text_v.change_show.connect(self.textViewShowOnOff)
        self.lc_text_v.change_select.connect(self.textViewSelectOnOff)
        grid.addWidget(self.lc_text_v, grid_row, 1, 1, 2)
        grid_row += 1

        # controls for map-relative polygon layer
        self.lc_poly = LayerControl(self, 'Polygon, map relative %s'
                                    % (str(MRPolyShowLevels) if MRPolyShowLevels else ''),
                                       selectable=True)
        self.lc_poly.change_add.connect(self.polyOnOff)     # tie to event handler(s)
        self.lc_poly.change_show.connect(self.polyShowOnOff)
        self.lc_poly.change_select.connect(self.polySelectOnOff)
        grid.addWidget(self.lc_poly, grid_row, 1, 1, 2)
        grid_row += 1

        # controls for view-relative polygon layer
        self.lc_poly_v = LayerControl(self, 'Polygon, view relative', selectable=True)
        self.lc_poly_v.change_add.connect(self.polyViewOnOff)    # tie to event handler(s)
        self.lc_poly_v.change_show.connect(self.polyViewShowOnOff)
        self.lc_poly_v.change_select.connect(self.polyViewSelectOnOff)
        grid.addWidget(self.lc_poly_v, grid_row, 1, 1, 2)
        grid_row += 1

        # controls for map-relative polyline layer
        self.lc_poll = LayerControl(self, 'Polyline, map relative %s'
                                    % (str(MRPolyShowLevels) if MRPolyShowLevels else ''),
                                       selectable=True)
        self.lc_poll.change_add.connect(self.polylineOnOff)     # tie to event handler(s)
        self.lc_poll.change_show.connect(self.polylineShowOnOff)
        self.lc_poll.change_select.connect(self.polylineSelectOnOff)
        grid.addWidget(self.lc_poll, grid_row, 1, 1, 2)
        grid_row += 1

        # controls for view-relative polyline layer
        self.lc_poll_v = LayerControl(self, 'Polyline, view relative', selectable=True)
        self.lc_poll_v.change_add.connect(self.polylineViewOnOff)    # tie to event handler(s)
        self.lc_poll_v.change_show.connect(self.polylineViewShowOnOff)
        self.lc_poll_v.change_select.connect(self.polylineViewSelectOnOff)
        grid.addWidget(self.lc_poll_v, grid_row, 1, 1, 2)
        grid_row += 1

        return grid_row

    def initMenu(self):
        """Add the 'Tilesets' menu to the app."""

        # create tileset menuitems
        menubar = self.menuBar()
        tilesets = menubar.addMenu('Tilesets')

        # this dict: id -> (display_name, module_name, action, tileset_obj)
        self.id2tiledata = {}

        # create the tileset menuitems, add to menu and connect to handler
        for (action_id, (name, module_name)) in enumerate(Tilesets):
            # create menu, connect to handler
            new_action = QAction(name, self, checkable=True)
            tilesets.addAction(new_action)
            action_plus_menuid = partial(self.change_tileset, action_id)
            new_action.triggered.connect(action_plus_menuid)

            # prepare the dict that handles importing tileset object
            self.id2tiledata[action_id] = (name, module_name, new_action, None)

            # check the default tileset
            if action_id == DefaultTilesetIndex:
                # put a check on the default tileset
                new_action.setChecked(True)

    def init_tiles(self):
        """Initialize the tileset manager.

        Return a reference to the manager object.
        """

        modules = []
        for (action_id, (name, module_name)) in enumerate(Tilesets):
            modules.append(module_name)

        return TilesetManager(modules)

    def change_tileset(self, menu_id):
        """Handle a tileset selection.

        menu_id  the index in self.id2tiledata of the required tileset
        """

        log('change_tileset: menu_id=%s' % str(menu_id))
        log('id2tiledata[]=%s' % str(self.id2tiledata))

        # ensure only one tileset is checked in the menu, the required one
        for (key, tiledata) in self.id2tiledata.items():
            (name, module_name, action, tile_obj) = tiledata
            action.setChecked(key == menu_id)

        # get information for the required tileset
        try:
            (name, module_name, action, new_tile_obj) = self.id2tiledata[menu_id]
        except KeyError:
            # badly formed self.id2tiledata element
            raise RuntimeError('self.id2tiledata is badly formed:\n%s'
                               % str(self.id2tiledata))

        log('name=%s, module_name=%s, new_tile_obj=%s'
                % (str(name), str(module_name), str(new_tile_obj)))

        if new_tile_obj is None:
            # haven't seen this tileset before, import and instantiate
            log("importing '%s' from pySlipQt" % str(module_name))
            obj = __import__('pySlipQt', globals(), locals(), [module_name])
            log('imported module=%s' % str(obj))
            log('imported module=%s' % str(dir(obj)))
            tileset = getattr(obj, module_name)
            log('tileset=%s' % str(tileset))
            tile_name = tileset.TilesetName
            log('tile_name=%s' % str(tile_name))
            new_tile_obj = tileset.Tiles()

            # update the self.id2tiledata element
            self.id2tiledata[menu_id] = (name, module_name, action, new_tile_obj)

        log('Before .ChangeTileset, new_tile_obj=%s' % str(new_tile_obj))
        self.pyslip.ChangeTileset(new_tile_obj)

    def onClose(self):
        """Application is closing."""

        pass

        #self.Close(True)

    def make_gui_level(self, parent):
        """Build the control that shows the level.

        parent  reference to parent

        Returns reference to containing sizer object.
        """

        # create objects
        txt = wx.StaticText(parent, wx.ID_ANY, 'Level: ')
        self.map_level = ROTextCtrl(parent, '', size=(30,-1),
                                    tooltip='Shows map zoom level')

        # lay out the controls
        sb = AppStaticBox(parent, 'Map level')
        box = wx.StaticBoxSizer(sb, orient=wx.HORIZONTAL)
        box.Add(txt, border=PackBorder, flag=(wx.ALIGN_CENTER_VERTICAL
                                              |wx.ALIGN_RIGHT|wx.LEFT))
        box.Add(self.map_level, proportion=0, border=PackBorder,
                flag=wx.LEFT|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)

        return box

    def make_gui_mouse(self, parent):
        """Build the mouse part of the controls part of GUI.

        parent  reference to parent

        Returns reference to containing sizer object.
        """

        # create objects
        txt = wx.StaticText(parent, wx.ID_ANY, 'Lon/Lat: ')
        self.mouse_position = ROTextCtrl(parent, '', size=(120,-1),
                                         tooltip=('Shows the mouse '
                                                  'longitude and latitude '
                                                  'on the map'))

        # lay out the controls
        sb = AppStaticBox(parent, 'Mouse position')
        box = wx.StaticBoxSizer(sb, orient=wx.HORIZONTAL)
        box.Add(txt, border=PackBorder, flag=(wx.ALIGN_CENTER_VERTICAL
                                     |wx.ALIGN_RIGHT|wx.LEFT))
        box.Add(self.mouse_position, proportion=0, border=PackBorder,
                flag=wx.RIGHT|wx.TOP|wx.BOTTOM)

        return box

    def make_gui_point(self, parent):
        """Build the points part of the controls part of GUI.

        parent  reference to parent

        Returns reference to containing sizer object.
        """

        # create widgets
        point_obj = LayerControl(parent, 'Points, map relative %s'
                                         % str(MRPointShowLevels),
                                 selectable=True)

        # tie to event handler(s)
        point_obj.Bind(EVT_ONOFF, self.pointOnOff)
        point_obj.Bind(EVT_SHOWONOFF, self.pointShowOnOff)
        point_obj.Bind(EVT_SELECTONOFF, self.pointSelectOnOff)

        return point_obj

    def make_gui_point_view(self, parent):
        """Build the view-relative points part of the GUI.

        parent  reference to parent

        Returns reference to containing sizer object.
        """

        # create widgets
        point_obj = LayerControl(parent, 'Points, view relative',
                                 selectable=True)

        # tie to event handler(s)
        point_obj.Bind(EVT_ONOFF, self.pointViewOnOff)
        point_obj.Bind(EVT_SHOWONOFF, self.pointViewShowOnOff)
        point_obj.Bind(EVT_SELECTONOFF, self.pointViewSelectOnOff)

        return point_obj

    def make_gui_image(self, parent):
        """Build the image part of the controls part of GUI.

        parent  reference to parent

        Returns reference to containing sizer object.
        """

        # create widgets
        image_obj = LayerControl(parent, 'Images, map relative %s'
                                         % str(MRImageShowLevels),
                                 selectable=True)

        # tie to event handler(s)
        image_obj.Bind(EVT_ONOFF, self.imageOnOff)
        image_obj.Bind(EVT_SHOWONOFF, self.imageShowOnOff)
        image_obj.Bind(EVT_SELECTONOFF, self.imageSelectOnOff)

        return image_obj

    def make_gui_image_view(self, parent):
        """Build the view-relative image part of the controls part of GUI.

        parent  reference to parent

        Returns reference to containing sizer object.
        """

        # create widgets
        image_obj = LayerControl(parent, 'Images, view relative',
                                 selectable=True)

        # tie to event handler(s)
        image_obj.Bind(EVT_ONOFF, self.imageViewOnOff)
        image_obj.Bind(EVT_SHOWONOFF, self.imageViewShowOnOff)
        image_obj.Bind(EVT_SELECTONOFF, self.imageViewSelectOnOff)

        return image_obj

    def make_gui_text(self, parent):
        """Build the map-relative text part of the controls part of GUI.

        parent  reference to parent

        Returns reference to containing sizer object.
        """

        # create widgets
        text_obj = LayerControl(parent,
                                'Text, map relative %s' % str(MRTextShowLevels),
                                selectable=True, editable=False)

        # tie to event handler(s)
        text_obj.Bind(EVT_ONOFF, self.textOnOff)
        text_obj.Bind(EVT_SHOWONOFF, self.textShowOnOff)
        text_obj.Bind(EVT_SELECTONOFF, self.textSelectOnOff)

        return text_obj

    def make_gui_text_view(self, parent):
        """Build the view-relative text part of the controls part of GUI.

        parent  reference to parent

        Returns reference to containing sizer object.
        """

        # create widgets
        text_view_obj = LayerControl(parent, 'Text, view relative',
                                     selectable=True)

        # tie to event handler(s)
        text_view_obj.Bind(EVT_ONOFF, self.textViewOnOff)
        text_view_obj.Bind(EVT_SHOWONOFF, self.textViewShowOnOff)
        text_view_obj.Bind(EVT_SELECTONOFF, self.textViewSelectOnOff)

        return text_view_obj

    def make_gui_poly(self, parent):
        """Build the map-relative polygon part of the controls part of GUI.

        parent  reference to parent

        Returns reference to containing sizer object.
        """

        # create widgets
        poly_obj = LayerControl(parent,
                                'Polygon, map relative %s'
                                     % str(MRPolyShowLevels),
                                selectable=True)

        # tie to event handler(s)
        poly_obj.Bind(EVT_ONOFF, self.polyOnOff)
        poly_obj.Bind(EVT_SHOWONOFF, self.polyShowOnOff)
        poly_obj.Bind(EVT_SELECTONOFF, self.polySelectOnOff)

        return poly_obj

    def make_gui_poly_view(self, parent):
        """Build the view-relative polygon part of the controls part of GUI.

        parent  reference to parent

        Returns reference to containing sizer object.
        """

        # create widgets
        poly_view_obj = LayerControl(parent, 'Polygon, view relative',
                                     selectable=True)

        # tie to event handler(s)
        poly_view_obj.Bind(EVT_ONOFF, self.polyViewOnOff)
        poly_view_obj.Bind(EVT_SHOWONOFF, self.polyViewShowOnOff)
        poly_view_obj.Bind(EVT_SELECTONOFF, self.polyViewSelectOnOff)

        return poly_view_obj

    def make_gui_polyline(self, parent):
        """Build the map-relative polyline part of the controls part of GUI.

        parent  reference to parent

        Returns reference to containing sizer object.
        """

        # create widgets
        poly_obj = LayerControl(parent,
                                'Polyline, map relative %s'
                                     % str(MRPolyShowLevels),
                                selectable=True)

        # tie to event handler(s)
        poly_obj.Bind(EVT_ONOFF, self.polylineOnOff)
        poly_obj.Bind(EVT_SHOWONOFF, self.polylineShowOnOff)
        poly_obj.Bind(EVT_SELECTONOFF, self.polylineSelectOnOff)

        return poly_obj

    def make_gui_polyline_view(self, parent):
        """Build the view-relative polyline part of the controls part of GUI.

        parent  reference to parent

        Returns reference to containing sizer object.
        """

        # create widgets
        poly_view_obj = LayerControl(parent, 'Polyline, view relative',
                                     selectable=True)

        # tie to event handler(s)
        poly_view_obj.Bind(EVT_ONOFF, self.polylineViewOnOff)
        poly_view_obj.Bind(EVT_SHOWONOFF, self.polylineViewShowOnOff)
        poly_view_obj.Bind(EVT_SELECTONOFF, self.polylineViewSelectOnOff)

        return poly_view_obj

    ######
    # demo control event handlers
    ######

##### map-relative point layer

    def pointOnOff(self, event):
        """Handle OnOff event for point layer control."""

        if event:
            self.point_layer = \
                self.pyslip.AddPointLayer(PointData, map_rel=True,
                                          colour=PointDataColour, radius=3,
                                          # offset points to exercise placement
                                          offset_x=0, offset_y=0, visible=True,
                                          show_levels=MRPointShowLevels,
                                          delta=DefaultPointMapDelta,
                                          placement='nw',   # check placement
                                          name='<pt_layer>')
        else:
            self.lc_point.set_show(True)       # set control state to 'normal'
            self.lc_point.set_select(False)

            self.pyslip.DeleteLayer(self.point_layer)
            self.point_layer = None

            if self.sel_point_layer:
                self.pyslip.DeleteLayer(self.sel_point_layer)
                self.sel_point_layer = None
                self.sel_point = None

    def pointShowOnOff(self, event):
        """Handle ShowOnOff event for point layer control."""

        if event:
            self.pyslip.ShowLayer(self.point_layer)
            if self.sel_point_layer:
                self.pyslip.ShowLayer(self.sel_point_layer)
        else:
            self.pyslip.HideLayer(self.point_layer)
            if self.sel_point_layer:
                self.pyslip.HideLayer(self.sel_point_layer)

    def pointSelectOnOff(self, event):
        """Handle SelectOnOff event for point layer control."""

        layer = self.point_layer
        if event:
            self.add_select_handler(layer, self.pointSelect)
            self.pyslip.SetLayerSelectable(layer, True)
        else:
            self.del_select_handler(layer)
            self.pyslip.SetLayerSelectable(layer, False)

    def pointSelect(self, event):
        """Handle map-relative point select exception from the widget.

        event.type       the layer type the select occurred on
        event.layer_id   ID of the layer the select occurred on
        event.mposn      mouse click in view coordinates
        event.vposn      ???
        event.selection  list of tuples (x,y,kwargs) of selected point(s)
                         (if None then no point(s) selected)
        event.relsel     relative selection (unused?)

        The selection could be a single or box select.

        The point select is designed to be select point(s) for on, then select
        point(s) again for off.  Clicking away from the already selected point
        doesn't remove previously selected point(s) if nothing is selected.  We
        do this to show the selection/deselection of point(s) is up to the user,
        not the widget.

        This code also shows how to combine handling of EventSelect and
        EventBoxSelect events.
        """

        if event.selection == self.sel_point:
            # same point(s) selected again, turn point(s) off
            self.pyslip.DeleteLayer(self.sel_point_layer)
            self.sel_point_layer = None
            self.sel_point = None
        elif event.selection:
            # some other point(s) selected, delete previous selection, if any
            if self.sel_point_layer:
                self.pyslip.DeleteLayer(self.sel_point_layer)

            # remember selection (need copy as highlight modifies attributes)
            self.sel_point = copy.deepcopy(event.selection)

            # choose different highlight colour for different type of selection
            selcolour = '#00ffff'
            if event.type == pySlipQt.PySlipQt.EVT_PYSLIPQT_SELECT: # TODO better visibility (like pySlip)
                selcolour = '#0000ff'

            # get selected points into form for display layer
            # delete 'colour' and 'radius' attributes as we want different values
            highlight = []
            for (x, y, d) in event.selection:
                del d['colour']     # AddLayer...() ensures keys exist
                del d['radius']
                highlight.append((x, y, d))

            # layer with highlight of selected poijnts
            self.sel_point_layer = \
                self.pyslip.AddPointLayer(highlight, map_rel=True,
                                          colour=selcolour,
                                          radius=5, visible=True,
                                          show_levels=MRPointShowLevels,
                                          name='<sel_pt_layer>')

            # make sure highlight layer is BELOW selected layer
            self.pyslip.PlaceLayerBelowLayer(self.sel_point_layer,
                                             self.point_layer)
        # else: we ignore an empty selection

        return True

##### view-relative point layer

    def pointViewOnOff(self, event):
        """Handle OnOff event for point view layer control."""

        if event:
            self.point_view_layer = \
                self.pyslip.AddPointLayer(PointViewData, map_rel=False,
                                          placement=PointViewDataPlacement,
                                          colour=PointViewDataColour, radius=1,
                                          delta=DefaultPointViewDelta,
                                          visible=True,
                                          name='<point_view_layer>')
        else:
            self.lc_point_v.set_show(True)       # set control state to 'normal'
            self.lc_point_v.set_select(False)

            self.pyslip.DeleteLayer(self.point_view_layer)
            self.point_view_layer = None
            if self.sel_point_view_layer:
                self.pyslip.DeleteLayer(self.sel_point_view_layer)
                self.sel_point_view_layer = None
                self.sel_point_view = None

    def pointViewShowOnOff(self, event):
        """Handle ShowOnOff event for point view layer control."""

        if event:
            self.pyslip.ShowLayer(self.point_view_layer)
            if self.sel_point_view_layer:
                self.pyslip.ShowLayer(self.sel_point_view_layer)
        else:
            self.pyslip.HideLayer(self.point_view_layer)
            if self.sel_point_view_layer:
                self.pyslip.HideLayer(self.sel_point_view_layer)

    def pointViewSelectOnOff(self, event):
        """Handle SelectOnOff event for point view layer control."""

        layer = self.point_view_layer
        if event:
            self.add_select_handler(layer, self.pointViewSelect)
            self.pyslip.SetLayerSelectable(layer, True)
        else:
            self.del_select_handler(layer)
            self.pyslip.SetLayerSelectable(layer, False)

    def pointViewSelect(self, event):
        """Handle view-relative point select exception from the widget.

        event.type       the event type
        event.layer_id   the ID of the layer that was selected
        event.selection  [list of] tuple (xgeo,ygeo) of selected point
                         (if None then no point(s) selected)
        event.data       userdata object of the selected point

        The selection could be a single or box select.

        The point select is designed to be click point for on, then any other
        select event turns that point off, whether there is a selection or not
        and whether the same point is selected or not.
        """

        # if there is a previous selection, remove it
        if self.sel_point_view_layer:
            self.pyslip.DeleteLayer(self.sel_point_view_layer)
            self.sel_point_view_layer = None

        if event.selection and event.selection != self.sel_point_view:
            # it's a box selection
            self.sel_point_view = event.selection

            # get selected points into form for display layer
            highlight = []
            for (x, y, d) in event.selection:
                del d['colour']
                del d['radius']
                highlight.append((x, y, d))

            # assume a box selection
            self.sel_point_view_layer = \
                self.pyslip.AddPointLayer(highlight, map_rel=False,
                                          placement='se',
                                          colour='#0000ff',
                                          radius=3, visible=True,
                                          name='<sel_pt_view_layer>')
        else:
            self.sel_point_view = None

        return True

##### map-relative image layer

    def imageOnOff(self, event):
        """Handle OnOff event for map-relative image layer control."""

        if event:
            self.image_layer = \
                self.pyslip.AddImageLayer(ImageData, map_rel=True,
                                          visible=True,
                                          delta=DefaultImageMapDelta,
                                          show_levels=MRImageShowLevels,
                                          name='<image_layer>')
        else:
            self.lc_image.set_show(True)       # set control state to 'normal'
            self.lc_image.set_select(False)

            self.pyslip.DeleteLayer(self.image_layer)
            self.image_layer = None
            if self.sel_image_layer:
                self.pyslip.DeleteLayer(self.sel_image_layer)
                self.sel_image_layer = None
                self.sel_image = None

    def imageShowOnOff(self, event):
        """Handle ShowOnOff event for image layer control."""

        if event:
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
        if event:
            self.add_select_handler(layer, self.imageSelect)
            self.pyslip.SetLayerSelectable(layer, True)
        else:
            self.del_select_handler(layer)
            self.pyslip.SetLayerSelectable(layer, False)

    def imageSelect(self, event):
        """Select event from the widget.

        event.type       the type of point selection: single or box
        event.selection  tuple (selection, data, relsel)
                         (if None then no point(s) selected)
        event.data       userdata object of the selected point

        The selection could be a single or box select.
        """

        #relsel = event.relsel

        # select again, turn selection off
        if event.selection == self.sel_image:
            self.pyslip.DeleteLayer(self.sel_image_layer)
            self.sel_image_layer = self.sel_image = None
        elif event.selection:
            # new image selected, show highlight
            if self.sel_image_layer:
                self.pyslip.DeleteLayer(self.sel_image_layer)
            self.sel_image = event.selection

            # get selected points into form for display layer
            new_points = []
            for p in event.selection:
                (x, y, d) = p
                del d['colour']
                del d['radius']
                new_points.append((x, y, d))

            self.sel_image_layer = \
                self.pyslip.AddPointLayer(new_points, map_rel=True,
                                          colour='#0000ff',
                                          radius=5, visible=True,
                                          show_levels=[3,4],
                                          name='<sel_pt_layer>')
            self.pyslip.PlaceLayerBelowLayer(self.sel_image_layer,
                                             self.image_layer)

        return True

    def imageBSelect(self, id, selection=None):
        """Select event from the widget."""

        # remove any previous selection
        if self.sel_image_layer:
            self.pyslip.DeleteLayer(self.sel_image_layer)
            self.sel_image_layer = None

        if selection:
            # get selected points into form for display layer
            points = []
            for (x, y, f, d) in selection:
                del d['colour']
                del d['radius']
                points.append((x, y, d))

            self.sel_image_layer = \
                self.pyslip.AddPointLayer(points, map_rel=True,
                                          colour='#e0e0e0',
                                          radius=13, visible=True,
                                          show_levels=[3,4],
                                          name='<boxsel_img_layer>')
            self.pyslip.PlaceLayerBelowLayer(self.sel_image_layer,
                                             self.image_layer)

        return True

##### view-relative image layer

    def imageViewOnOff(self, event):
        """Handle OnOff event for view-relative image layer control.
        
        event  the state of the leyer control master checkbox
        """

        if event:
            self.image_view_layer = \
                self.pyslip.AddImageLayer(ImageViewData, map_rel=False,
                                          delta=DefaultImageViewDelta,
                                          visible=True,
                                          name='<image_view_layer>')
        else:
            self.lc_image_v.set_show(True)       # set control state to 'normal'
            self.lc_image_v.set_select(False)

            self.pyslip.DeleteLayer(self.image_view_layer)
            self.image_view_layer = None
            if self.sel_image_view_layer:
                self.pyslip.DeleteLayer(self.sel_image_view_layer)
                self.sel_image_view_layer = None
            if self.sel_imagepoint_view_layer:
                self.pyslip.DeleteLayer(self.sel_imagepoint_view_layer)
                self.sel_imagepoint_view_layer = None

    def imageViewShowOnOff(self, event):
        """Handle ShowOnOff event for image layer control."""

        if event:
            self.pyslip.ShowLayer(self.image_view_layer)
            if self.sel_image_view_layer:
                self.pyslip.ShowLayer(self.sel_image_view_layer)
            if self.sel_imagepoint_view_layer:
                self.pyslip.ShowLayer(self.sel_imagepoint_view_layer)
        else:
            self.pyslip.HideLayer(self.image_view_layer)
            if self.sel_image_view_layer:
                self.pyslip.HideLayer(self.sel_image_view_layer)
            if self.sel_imagepoint_view_layer:
                self.pyslip.HideLayer(self.sel_imagepoint_view_layer)

    def imageViewSelectOnOff(self, event):
        """Handle SelectOnOff event for image layer control."""

        layer = self.image_view_layer
        if event:
            self.add_select_handler(layer, self.imageViewSelect)
            self.pyslip.SetLayerSelectable(layer, True)
        else:
            self.del_select_handler(layer)
            self.pyslip.SetLayerSelectable(layer, False)

    def imageViewSelect(self, event):
        """View-relative image select event from the widget.

        event  the event that contains these attributes:
                   selection  [list of] tuple (xgeo,ygeo) of selected point
                              (if None then no point(s) selected)
                   relsel     relative position of single point select,
                              None if box select

        The selection could be a single or box select.

        The selection mode is different here.  An empty selection will remove
        any current selection.  This shows the flexibility that user code
        can implement.

        The code below doesn't assume a placement of the selected image, it
        figures out the correct position of the 'highlight' layers.  This helps
        with debugging, as we can move the compass rose anywhere we like.
        """

        selection = event.selection
        relsel = event.relsel       # None if box select

        # only one image selectable, remove old selections (if any)
        if self.sel_image_view_layer:
            self.pyslip.DeleteLayer(self.sel_image_view_layer)
            self.sel_image_view_layer = None
        if self.sel_imagepoint_view_layer:
            self.pyslip.DeleteLayer(self.sel_imagepoint_view_layer)
            self.sel_imagepoint_view_layer = None

        if selection:
            # figure out compass rose attributes
            attr_dict = ImageViewData[0][3]
            img_placement = attr_dict['placement']

            self.sel_imagepoint_view_layer = None
            if relsel:
                # unpack event relative selection point
                (sel_x, sel_y) = relsel     # select relative point in image

# FIXME  This should be cleaner, user shouldn't have to know internal structure
# FIXME  or fiddle with placement perturbations

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
                self.sel_imagepoint_view_layer = \
                    self.pyslip.AddPointLayer((point,), map_rel=False,
                                              colour='green',
                                              radius=5, visible=True,
                                              placement=img_placement,
                                              name='<sel_image_view_point>')

            # add polygon outline around image
            p_dict = {'placement': img_placement, 'width': 3, 'colour': 'green', 'closed': True}
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
            self.sel_image_view_layer = \
                self.pyslip.AddPolygonLayer((pdata,), map_rel=False,
                                            name='<sel_image_view_outline>',
                                           )

        return True

##### map-relative text layer

    def textOnOff(self, event):
        """Handle OnOff event for map-relative text layer control."""

        if event:
            self.text_layer = \
                self.pyslip.AddTextLayer(TextData, map_rel=True,
                                         name='<text_layer>', visible=True,
                                         delta=DefaultTextMapDelta,
                                         show_levels=MRTextShowLevels,
                                         placement='ne')
        else:
            self.lc_text.set_show(True)       # set control state to 'normal'
            self.lc_text.set_select(False)
            self.pyslip.DeleteLayer(self.text_layer)
            if self.sel_text_layer:
                self.pyslip.DeleteLayer(self.sel_text_layer)
                self.sel_text_layer = None
                self.sel_text_highlight = None

    def textShowOnOff(self, event):
        """Handle ShowOnOff event for text layer control."""

        if event:
            if self.text_layer:
                self.pyslip.ShowLayer(self.text_layer)
            if self.sel_text_layer:
                self.pyslip.ShowLayer(self.sel_text_layer)
        else:
            if self.text_layer:
                self.pyslip.HideLayer(self.text_layer)
            if self.sel_text_layer:
                self.pyslip.HideLayer(self.sel_text_layer)

    def textSelectOnOff(self, event):
        """Handle SelectOnOff event for text layer control."""

        layer = self.text_layer
        if event:
            self.add_select_handler(layer, self.textSelect)
            self.pyslip.SetLayerSelectable(layer, True)
        else:
            self.del_select_handler(layer)
            self.pyslip.SetLayerSelectable(layer, False)


    def textSelect(self, event):
        """Map-relative text select event from the widget.

        event.type       the type of point selection: single or box
        event.selection  [list of] tuple (xgeo,ygeo) of selected point
                         (if None then no point(s) selected)

        The selection could be a single or box select.

        The selection mode here is more standard: empty select turns point(s)
        off, selected points reselection leaves points selected.
        """

        selection = event.selection

        if self.sel_text_layer:
            # turn previously selected point(s) off
            self.pyslip.DeleteLayer(self.sel_text_layer)
            self.sel_text_layer = None

        if selection:
            # get selected points into form for display layer
            points = []
            for (x, y, d) in selection:
                del d['colour']     # remove point attributes, want different
                del d['radius']
                del d['offset_x']   # remove offsets, we want point not text
                del d['offset_y']
                points.append((x, y, d))

            self.sel_text_layer = \
                self.pyslip.AddPointLayer(points, map_rel=True,
                                          colour='#0000ff',
                                          radius=5, visible=True,
                                          show_levels=MRTextShowLevels,
                                          name='<sel_text_layer>')
            self.pyslip.PlaceLayerBelowLayer(self.sel_text_layer,
                                             self.text_layer)

        return True

##### view-relative text layer

    def textViewOnOff(self, event):
        """Handle OnOff event for view-relative text layer control."""

        if event:
            self.text_view_layer = \
                self.pyslip.AddTextLayer(TextViewData, map_rel=False,
                                         name='<text_view_layer>',
                                         delta=DefaultTextViewDelta,
                                         placement=TextViewDataPlace,
                                         visible=True,
                                         fontsize=24, textcolour='#0000ff',
                                         offset_x=TextViewDataOffX,
                                         offset_y=TextViewDataOffY)
        else:
            self.lc_text_v.set_show(True)       # set control state to 'normal'
            self.lc_text_v.set_select(False)

            self.pyslip.DeleteLayer(self.text_view_layer)
            self.text_view_layer = None
            if self.sel_text_view_layer:
                self.pyslip.DeleteLayer(self.sel_text_view_layer)
                self.sel_text_view_layer = None

    def textViewShowOnOff(self, event):
        """Handle ShowOnOff event for view text layer control."""

        if event:
            self.pyslip.ShowLayer(self.text_view_layer)
            if self.sel_text_view_layer:
                self.pyslip.ShowLayer(self.sel_text_view_layer)
        else:
            self.pyslip.HideLayer(self.text_view_layer)
            if self.sel_text_view_layer:
                self.pyslip.HideLayer(self.sel_text_view_layer)

    def textViewSelectOnOff(self, event):
        """Handle SelectOnOff event for view text layer control."""

        layer = self.text_view_layer
        if event:
            self.add_select_handler(layer, self.textViewSelect)
            self.pyslip.SetLayerSelectable(layer, True)
        else:
            self.del_select_handler(layer)
            self.pyslip.SetLayerSelectable(layer, False)

    def textViewSelect(self, event):
        """View-relative text select event from the widget.

        event  the event that contains these attributes:
                   type       the type of point selection: single or box
                   selection  [list of] tuple (xgeo,ygeo) of selected point
                              (if None then no point(s) selected)

        The selection could be a single or box select.

        The selection mode here is more standard: empty select turns point(s)
        off, selected points reselection leaves points selected.
        """

        selection = event.selection

        # turn off any existing selection
        if self.sel_text_view_layer:
            self.pyslip.DeleteLayer(self.sel_text_view_layer)
            self.sel_text_view_layer = None

        if selection:
            # get selected points into form for point display layer
            points = []
            for (x, y, d) in selection:
                del d['colour']     # want to override colour, radius
                del d['radius']
                points.append((x, y, d))

            self.sel_text_view_layer = \
                self.pyslip.AddPointLayer(points, map_rel=False,
                                          colour='black',
                                          radius=5, visible=True,
                                          show_levels=MRTextShowLevels,
                                          name='<sel_text_view_layer>')
            self.pyslip.PlaceLayerBelowLayer(self.sel_text_view_layer,
                                             self.text_view_layer)

        return True

##### map-relative polygon layer

    def polyOnOff(self, event):
        """Handle OnOff event for map-relative polygon layer control."""

        if event:
            self.poly_layer = \
                self.pyslip.AddPolygonLayer(PolyData, map_rel=True,
                                            visible=True,
                                            delta=DefaultPolygonMapDelta,
                                            show_levels=MRPolyShowLevels,
                                            name='<poly_layer>')
        else:
            self.lc_poly.set_show(True)       # set control state to 'normal'
            self.lc_poly.set_select(False)

            self.pyslip.DeleteLayer(self.poly_layer)
            self.poly_layer = None

            if self.sel_poly_layer:
                self.pyslip.DeleteLayer(self.sel_poly_layer)
                self.sel_poly_layer = None
                self.sel_poly_point = None

    def polyShowOnOff(self, event):
        """Handle ShowOnOff event for polygon layer control."""

        if event:
            self.pyslip.ShowLayer(self.poly_layer)
            if self.sel_poly_layer:
                self.pyslip.ShowLayer(self.sel_poly_layer)
        else:
            self.pyslip.HideLayer(self.poly_layer)
            if self.sel_poly_layer:
                self.pyslip.HideLayer(self.sel_poly_layer)

    def polySelectOnOff(self, event):
        """Handle SelectOnOff event for polygon layer control."""

        layer = self.poly_layer
        if event:
            self.add_select_handler(layer, self.polySelect)
            self.pyslip.SetLayerSelectable(layer, True)
        else:
            self.del_select_handler(layer)
            self.pyslip.SetLayerSelectable(layer, False)

    def polySelect(self, event):
        """Map- and view-relative polygon select event from the widget.

        event  the event that contains these attributes:
                   type       the type of point selection: single or box
                   selection  [list of] tuple (xgeo,ygeo) of selected point
                              (if None then no point(s) selected)

        The selection could be a single or box select.

        Select a polygon to turn it on, any other polygon selection turns
        it off, unless previous selection again selected.
        """

        # .seletion: [(poly,attr), ...]
        selection = event.selection

        # turn any previous selection off
        if self.sel_poly_layer:
            self.pyslip.DeleteLayer(self.sel_poly_layer)
            self.sel_poly_layer = None

        # box OR single selection
        if selection:
            # get selected polygon points into form for point display layer
            points = []
            for (poly, d) in selection:
                try:
                    del d['colour']
                except KeyError:
                    pass
                try:
                    del d['radius']
                except KeyError:
                    pass
                for (x, y) in poly:
                    points.append((x, y, d))

            self.sel_poly_layer = \
                self.pyslip.AddPointLayer(points, map_rel=True,
                                          colour='#ff00ff',
                                          radius=5, visible=True,
                                          show_levels=[3,4],
                                          name='<sel_poly>')

        return True

##### view-relative polygon layer

    def polyViewOnOff(self, event):
        """Handle OnOff event for map-relative polygon layer control."""

        if event:
            self.poly_view_layer = \
                self.pyslip.AddPolygonLayer(PolyViewData, map_rel=False,
                                            delta=DefaultPolygonViewDelta,
                                            name='<poly_view_layer>',
                                            placement='cn', visible=True,
                                            fontsize=24, colour='#0000ff')
        else:
            self.lc_poly_v.set_show(True)       # set control state to 'normal'
            self.lc_poly_v.set_select(False)

            self.pyslip.DeleteLayer(self.poly_view_layer)
            self.poly_view_layer = None

            if self.sel_poly_view_layer:
                self.pyslip.DeleteLayer(self.sel_poly_view_layer)
                self.sel_poly_view_layer = None
                self.sel_poly_view_point = None

    def polyViewShowOnOff(self, event):
        """Handle ShowOnOff event for polygon layer control."""

        if event:
            self.pyslip.ShowLayer(self.poly_view_layer)
            if self.sel_poly_view_layer:
                self.pyslip.ShowLayer(self.sel_poly_view_layer)
        else:
            self.pyslip.HideLayer(self.poly_view_layer)
            if self.sel_poly_view_layer:
                self.pyslip.HideLayer(self.sel_poly_view_layer)

    def polyViewSelectOnOff(self, event):
        """Handle SelectOnOff event for polygon layer control."""

        layer = self.poly_view_layer
        if event:
            self.add_select_handler(layer, self.polyViewSelect)
            self.pyslip.SetLayerSelectable(layer, True)
        else:
            self.del_select_handler(layer)
            self.pyslip.SetLayerSelectable(layer, False)

    def polyViewSelect(self, event):
        """View-relative polygon select event from the widget.

        event  the event that contains these attributes:
                   type       the type of point selection: single or box
                   selection  tuple (sel, udata, None) defining the selected
                              polygon (if None then no point(s) selected)

        The selection could be a single or box select.
        """

        selection = event.selection

        # point select, turn any previous selection off
        if self.sel_poly_view_layer:
            self.pyslip.DeleteLayer(self.sel_poly_view_layer)
            self.sel_poly_view_layer = None

        # for box OR single selection
        if selection:
            # get selected polygon points into form for point display layer
            points = []
            for (poly, d) in selection:
                try:
                    del d['colour']
                except KeyError:
                    pass
                try:
                    del d['radius']
                except KeyError:
                    pass
                for (x, y) in poly:
                    points.append((x, y, d))

            self.sel_poly_view_layer = \
                self.pyslip.AddPointLayer(points, map_rel=False,
                                          colour='#ff00ff',
                                          radius=5, visible=True,
                                          show_levels=[3,4],
                                          name='<sel_view_poly>')

        return True

##### map-relative polyline layer

    def polylineOnOff(self, event):
        """Handle OnOff event for map-relative polyline layer control."""

        if event:
            self.polyline_layer = \
                self.pyslip.AddPolylineLayer(PolylineData, map_rel=True,
                                             visible=True,
                                             delta=DefaultPolylineMapDelta,
                                             show_levels=MRPolyShowLevels,
                                             name='<polyline_layer>')
        else:
            self.lc_poll.set_show(True)       # set control state to 'normal'
            self.lc_poll.set_select(False)

            self.pyslip.DeleteLayer(self.polyline_layer)
            self.polyline_layer = None

            if self.sel_polyline_layer:
                self.pyslip.DeleteLayer(self.sel_polyline_layer)
                self.sel_polyline_layer = None
                self.sel_polyline_point = None
            if self.sel_polyline_layer2:
                self.pyslip.DeleteLayer(self.sel_polyline_layer2)
                self.sel_polyline_layer2 = None

    def polylineShowOnOff(self, event):
        """Handle ShowOnOff event for polycwlinegon layer control."""

        if event:
            self.pyslip.ShowLayer(self.polyline_layer)
            if self.sel_polyline_layer:
                self.pyslip.ShowLayer(self.sel_polyline_layer)
            if self.sel_polyline_layer2:
                self.pyslip.ShowLayer(self.sel_polyline_layer2)
        else:
            self.pyslip.HideLayer(self.polyline_layer)
            if self.sel_polyline_layer:
                self.pyslip.HideLayer(self.sel_polyline_layer)
            if self.sel_polyline_layer2:
                self.pyslip.HideLayer(self.sel_polyline_layer2)

    def polylineSelectOnOff(self, event):
        """Handle SelectOnOff event for polyline layer control."""

        layer = self.polyline_layer
        if event:
            self.add_select_handler(layer, self.polylineSelect)
            self.pyslip.SetLayerSelectable(layer, True)
        else:
            self.del_select_handler(layer)
            self.pyslip.SetLayerSelectable(layer, False)

    def polylineSelect(self, event):
        """Map- and view-relative polyline select event from the widget.

        event  the event that contains these attributes:
                   type       the type of point selection: single or box
                   selection  [list of] tuple (xgeo,ygeo) of selected point
                              (if None then no point(s) selected)
                   relsel     a tuple (p1,p2) of polyline segment

        The selection could be a single or box select.

        Select a polyline to turn it on, any other polyline selection turns
        it off, unless previous selection again selected.
        """

        # .seletion: [(poly,attr), ...]
        selection = event.selection
        relsel = event.relsel

        # turn any previous selection off
        if self.sel_polyline_layer:
            self.pyslip.DeleteLayer(self.sel_polyline_layer)
            self.sel_polyline_layer = None
        if self.sel_polyline_layer2:
            self.pyslip.DeleteLayer(self.sel_polyline_layer2)
            self.sel_polyline_layer2 = None

        # box OR single selection
        if selection:
            # show segment selected first, if any
            if relsel:
                self.sel_polyline_layer2 = \
                    self.pyslip.AddPointLayer(relsel, map_rel=True,
                                              colour='#40ff40',
                                              radius=5, visible=True,
                                              show_levels=[3,4],
                                              name='<sel_polyline2>')

            # get selected polygon points into form for point display layer
            points = []
            for (poly, d) in selection:
                try:
                    del d['colour']
                except KeyError:
                    pass
                try:
                    del d['radius']
                except KeyError:
                    pass
                for (x, y) in poly:
                    points.append((x, y, d))

            self.sel_polyline_layer = \
                self.pyslip.AddPointLayer(points, map_rel=True,
                                          colour='#ff00ff',
                                          radius=3, visible=True,
                                          show_levels=[3,4],
                                          name='<sel_polyline>')
        return True

##### view-relative polyline layer

    def polylineViewOnOff(self, event):
        """Handle OnOff event for map-relative polyline layer control."""

        if event:
            self.polyline_view_layer = \
                self.pyslip.AddPolylineLayer(PolylineViewData, map_rel=False,
                                             delta=DefaultPolylineViewDelta,
                                             name='<polyline_view_layer>',
                                             placement='cn', visible=True,
                                             fontsize=24, colour='#0000ff')
        else:
            self.lc_poll_v.set_show(True)       # set control state to 'normal'
            self.lc_poll_v.set_select(False)

            self.pyslip.DeleteLayer(self.polyline_view_layer)
            self.polyline_view_layer = None

            if self.sel_polyline_view_layer:
                self.pyslip.DeleteLayer(self.sel_polyline_view_layer)
                self.sel_polyline_view_layer = None
                self.sel_polyline_view_point = None

            if self.sel_polyline_view_layer2:
                self.pyslip.DeleteLayer(self.sel_polyline_view_layer2)
                self.sel_polyline_view_layer2 = None

    def polylineViewShowOnOff(self, event):
        """Handle ShowOnOff event for polyline layer control."""

        if event:
            self.pyslip.ShowLayer(self.polyline_view_layer)
            if self.sel_polyline_view_layer:
                self.pyslip.ShowLayer(self.sel_polyline_view_layer)
            if self.sel_polyline_view_layer2:
                self.pyslip.ShowLayer(self.sel_polyline_view_layer2)
        else:
            self.pyslip.HideLayer(self.polyline_view_layer)
            if self.sel_polyline_view_layer:
                self.pyslip.HideLayer(self.sel_polyline_view_layer)
            if self.sel_polyline_view_layer2:
                self.pyslip.HideLayer(self.sel_polyline_view_layer2)

    def polylineViewSelectOnOff(self, event):
        """Handle SelectOnOff event for polyline layer control."""

        layer = self.polyline_view_layer
        if event:
            self.add_select_handler(layer, self.polylineViewSelect)
            self.pyslip.SetLayerSelectable(layer, True)
        else:
            self.del_select_handler(layer)
            self.pyslip.SetLayerSelectable(layer, False)

    def polylineViewSelect(self, event):
        """View-relative polyline select event from the widget.

        event  the event that contains these attributes:
                   type       the type of point selection: single or box
                   selection  tuple (sel, udata, None) defining the selected
                              polyline (if None then no point(s) selected)

        The selection could be a single or box select.
        """

        selection = event.selection
        relsel = event.relsel

        # point select, turn any previous selection off
        if self.sel_polyline_view_layer:
            self.pyslip.DeleteLayer(self.sel_polyline_view_layer)
            self.sel_polyline_view_layer = None
        if self.sel_polyline_view_layer2:
            self.pyslip.DeleteLayer(self.sel_polyline_view_layer2)
            self.sel_polyline_view_layer2 = None

        # for box OR single selection
        if selection:
            # first, display selected segment
            if relsel:
                # get original polyline attributes, get placement and offsets
                (_, attributes) = PolylineViewData[0]
                place = attributes.get('placement', None)
                offset_x = attributes.get('offset_x', 0)
                offset_y = attributes.get('offset_y', 0)

                self.sel_polyline_view_layer2 = \
                    self.pyslip.AddPointLayer(relsel, map_rel=False,
                                              placement=place,
                                              offset_x=offset_x,
                                              offset_y=offset_y,
                                              colour='#4040ff',
                                              radius=5, visible=True,
                                              show_levels=[3,4],
                                              name='<sel_view_polyline2>')

            # get selected polyline points into form for point display layer
            points = []
            for (poly, d) in selection:
                try:
                    del d['colour']
                except KeyError:
                    pass
                try:
                    del d['radius']
                except KeyError:
                    pass
                for (x, y) in poly:
                    points.append((x, y, d))

            self.sel_polyline_view_layer = \
                self.pyslip.AddPointLayer(points, map_rel=False,
                                          colour='#ff00ff',
                                          radius=3, visible=True,
                                          show_levels=[3,4],
                                          name='<sel_view_polyline>')

        return True

    def level_change_event(self, event):
        """Handle a "level change" event from the pySlipQt widget.
        
        event.type  the type of event
        event.level  the new map level
        """

        self.map_level.set_text(str(event.level))

    def mouse_posn_event(self, event):
        """Handle a "mouse position" event from the pySlipQt widget.
       
        The 'event' object has these attributes:
            event.etype  the type of event
            event.mposn  the new mouse position on the map (xgeo, ygeo)
            event.vposn  the new mouse position on the view (x, y)
        """

        if event.mposn:
            (lon, lat) = event.mposn
            # we clamp the lon/lat to zero here since we don't want small
            # negative values displaying as "-0.00"
            if abs(lon) < 0.01:
                lon = 0.0
            if abs(lat) < 0.01:
                lat = 0.0
            self.mouse_position.set_text('%.2f/%.2f' % (lon, lat))
        else:
            self.mouse_position.set_text('')

    def select_event(self, event):
        """Handle a single select click.

        event.type       the event type number
        event.mposn      select point tuple in map (geo) coordinates: (xgeo, ygeo)
        event.vposn      select point tuple in view coordinates: (xview, yview)
        event.layer_id   the ID of the layer containing the selected object (or None)
        event.selection  a tuple (x,y,attrib) defining the position of the object selected (or [] if no selection)
        event.data       the user-supplied data object for the selected object (or [] if no selection)
        event.relsel     relative selection point inside a single selected image (or [] if no selection)

        Just look at 'event.type' to decide what handler to call and pass
        'event' through to the handler.
        """

        self.dump_event('select_event: event:', event)

        self.demo_select_dispatch.get(event.layer_id, self.null_handler)(event)

    ######
    # Small utility routines
    ######

    def unimplemented(self, msg):
        """Issue an "Sorry, ..." message."""

        self.pyslip.warn('Sorry, %s is not implemented at the moment.' % msg)

    def dump_event(self, msg, event):
        """Dump an event to the log.

        Print attributes and values for non_dunder attributes.
        """

        log('dump_event: %s' % msg)
        for attr in dir(event):
            if not attr.startswith('__'):
                log('    event.%s=%s' % (attr, getattr(event, attr)))

    ######
    # Finish initialization of data, etc
    ######

    def initData(self):
        global PointData, PointDataColour, PointViewDataPlacement
        global PointViewData, PointViewDataColour
        global ImageData
        global ImageViewData
        global TextData
        global TextViewData
        global TextViewDataPlace, TextViewDataOffX, TextViewDataOffY
        global PolyData, PolyViewData
        global PolylineData, PolylineViewData
        global CR_Width, CR_Height

        # create PointData - lots of it to test handling
        PointData = []
        for lon in range(-70, 290+1, 5):
            for lat in range(-65, 65+1, 5):
                udata = 'point(%s,%s)' % (str(lon), str(lat))
                PointData.append((lon, lat, {'data': udata}))
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
        PointViewDataColour = '#00000040'	# transparent
        PointViewDataPlacement = 'se'

        # create image data - shipwrecks off the Australian east coast
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

        ImageViewData = [(0, 0, CompassRoseGraphic, {'placement': 'ne',
                                                     'data': 'compass rose'})]

        text_placement = {'placement': 'se'}
        transparent_placement = {'placement': 'se', 'colour': '#00000040'}
        capital = {'placement': 'se', 'fontsize': 14, 'colour': 'red',
                   'textcolour': 'red'}
        capital_sw = {'placement': 'sw', 'fontsize': 14, 'colour': 'red',
                      'textcolour': 'red'}
        TextData = [
                    (151.20, -33.85, 'Sydney', text_placement),
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
                    (143.1048, -5.4646, 'Porgera', text_placement),
                    (103.833333, 1.283333, 'Singapore', capital),
                    (101.683333, 3.133333, 'Kuala Lumpur', capital_sw),
                    (106.822922, -6.185451, 'Jakarta', capital),
                    (110.364444, -7.801389, 'Yogyakarta', text_placement),
                    (121.050, 14.600, 'Manila', capital),
                    (271.74, +40.11, 'Champaign', text_placement),
                    (160.0, -30.0, 'Agnes Napier - 1855',
                        {'placement': 'cw', 'offset_x': 20, 'colour': 'green'}),
                    (145.0, -11.0, 'Venus - 1826',
                        {'placement': 'sw', 'colour': 'green'}),
                    (156.0, -23.0, 'Wolverine - 1879',
                        {'placement': 'ce', 'colour': 'green'}),
                    (150.0, -15.0, 'Thomas Day - 1884',
                        {'colour': 'green'}),
                    (165.0, -19.0, 'Sybil - 1902',
                        {'placement': 'cw', 'colour': 'green'}),
                    (158.55, -19.98, 'Prince of Denmark - 1863',
                        {'placement': 'nw', 'offset_x': 20, 'colour': 'green'}),
                    (146.867525, -19.152182, 'Moltke - 1911',
                        {'placement': 'ce', 'offset_x': 20, 'colour': 'green'}),
                   ]
        if sys.platform != 'win32':
            # TODO: check if this works under Windows
            TextData.extend([
                    (110.490, 24.780, '阳朔县 (Yangshuo)', {'placement': 'sw'}),
                    (117.183333, 39.133333, '天津市 (Tianjin)', {'placement': 'sw'}),
                    (106.36, +10.36, 'Mỹ Tho', {'placement': 'ne'}),
                    (105.85, +21.033333, 'Hà Nội', capital),
                    (109.18333, 12.25, 'Nha Trang', {'placement': 'sw'}),
                    (106.681944, 10.769444, 'Thành phố Hồ Chí Minh',
                        {'placement': 'sw'}),
                    (132.47, +34.44, '広島市 (Hiroshima City)',
                        {'placement': 'nw'}),
                    (114.000, +22.450, '香港 (Hong Kong)', text_placement),
                    (98.392, 7.888, 'ภูเก็ต (Phuket)', text_placement),
                    ( 96.16, +16.80, 'ရန်ကုန် (Yangon)', capital),
                    (104.93, +11.54, ' ភ្នំពេញ (Phnom Penh)', capital),
                    (100.49, +13.75, 'กรุงเทพมหานคร (Bangkok)', capital),
                    ( 77.56, +34.09, 'གླེ་(Leh)', text_placement),
                    (84.991275, 24.695102, 'बोधगया (Bodh Gaya)', text_placement)
                        ])

        TextViewData = [(0, 0, '%s %s' % (DemoName, DemoVersion))]
        TextViewDataPlace = 'cn'
        TextViewDataOffX = 0
        TextViewDataOffY = 3

        PolyData = [(((150.0,10.0),(160.0,20.0),(170.0,10.0),(165.0,0.0),(155.0,0.0)),
                      {'width': 3, 'colour': 'blue', 'closed': True}),
                    (((165.0,-35.0),(175.0,-35.0),(175.0,-45.0),(165.0,-45.0)),
                      {'width': 10, 'colour': '#00ff00c0', 'filled': True,
                       'fillcolour': '#ffff0040'}),
                    (((190.0,-30.0),(220.0,-50.0),(220.0,-30.0),(190.0,-50.0)),
                      {'width': 3, 'colour': 'green', 'filled': True,
                       'fillcolour': 'yellow'}),
                    (((190.0,+50.0),(220.0,+65.0),(220.0,+50.0),(190.0,+65.0)),
                      {'width': 10, 'colour': '#00000040'})]

        PolyViewData = [(((230,0),(230,40),(-230,40),(-230,0)),
                        {'width': 3, 'colour': '#00ff00ff', 'closed': True,
                         'placement': 'cn', 'offset_y': 1})]

        PolylineData = [(((150.0,10.0),(160.0,20.0),(170.0,10.0),(165.0,0.0),(155.0,0.0)),
                          {'width': 3, 'colour': 'blue'}),
                        (((185.0,10.0),(185.0,20.0),(180.0,10.0),(175.0,0.0),(185.0,0.0)),
                          {'width': 3, 'colour': 'red'})]

        PolylineViewData = [(((50,100),(100,50),(150,100),(100,150)),
                            {'width': 3, 'colour': '#00ffffff', 'placement': 'cn'}),
                            (((100,250),(50,300),(100,350),(150,300)),
                            {'width': 3, 'colour': '#0000ffff', 'placement': 'cn'})]

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

        self.poly_layer = None
        self.sel_poly_layer = None
        self.sel_poly = None

        self.poly_view_layer = None
        self.sel_poly_view_layer = None
        self.sel_poly = None

        self.polyline_layer = None
        self.sel_polyline_layer = None
        self.sel_polyline_layer2 = None
        self.sel_polyline = None

        self.polyline_view_layer = None
        self.sel_polyline_view_layer = None
        self.sel_polyline_view_layer2 = None
        self.sel_polyline = None

        # get width and height of the compass rose image
        cr_img = QPixmap(CompassRoseGraphic)
        size = cr_img.size()
        CR_Height = size.height()
        CR_Width = size.width()

        # set initial view position
        self.map_level.set_text('%d' % InitViewLevel)

    ######
    # Exception handlers
    ######

    def null_handler(self, event):
        """Routine to handle unexpected events."""

        print('ERROR: null_handler!?')
        log('ERROR: null_handler!?')

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
# Main code
###############################################################################

def usage(msg=None):
    if msg:
        print(('*'*80 + '\n%s\n' + '*'*80) % msg)
    print(__doc__)

# our own handler for uncaught exceptions
def excepthook(type, value, tback):
    msg = '\n' + '=' * 80
    msg += '\nUncaught exception:\n'
    msg += ''.join(traceback.format_exception(type, value, tback))
    msg += '=' * 80 + '\n'
    log(msg)
    print(msg)
    sys.exit(1)

# plug our handler into the python system
sys.excepthook = excepthook

# parse the CLI params
argv = sys.argv[1:]

try:
    (opts, args) = getopt.getopt(argv, 'd:h', ['debug=', 'help'])
except getopt.error:
    usage()
    sys.exit(1)

debug = 10

for (opt, param) in opts:
    if opt in ['-d', '--debug']:
        debug = param
    elif opt in ['-h', '--help']:
        usage()
        sys.exit(0)

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

# start the app
app = QApplication(args)
ex = PySlipQtDemo()
sys.exit(app.exec_())

