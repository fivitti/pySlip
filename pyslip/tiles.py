#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A _base_ Tiles object for pySlip tiles.

All tile sources should inherit from this base class.
For example, see gmt_local_tiles.py and osm_tiles.py.
"""

import os
import glob
import wx
import pycacheback


######
# Base class for a tile source - handles access to a source of tiles.
######

class Tiles(object):

    DefaultTilesDir = '_=TILES=_'

    """An object to source tiles for pyslip."""

    def __init__(self, tiles, start_level=None, min_level=None, max_level=None):
        """Initialise a Tiles instance.

        tiles        tile cache directory, may contain tiles
        start_level  the level to start on'
        """

        # this should be overridden!
        raise Exception('You must override Tiles.__init__()')

    def SetAvailableCallback(self, callback):
        """Set the "tile now available" callback routine.

        callback  function with signature callback(level, x, y, image, bitmap)

        where 'level' is the level of the tile, 'x' and 'y' are
        the coordinates of the tile and 'image' and 'bitmap' are tile data.
        """

        raise Exception('You need to override Tiles.SetAvailableCallback()')

    def UseLevel(self, level):
        """Prepare to serve tiles from the required level.

        level  The required level

        Returns None if unsuccessful, else something non-None.

        This is dependant on tiles, coordinate system syste, etc, so must
        be fully implemented in child classes.
        """

        # don't forget to cancel any outstanding requests from servers

        raise Exception('You must override Tiles.UseLevel()')

    def GetTile(self, x, y):
        """Get bitmap for tile at tile coords (x, y) and current level.

        x  X coord of tile required (tile coordinates)
        y  Y coord of tile required (tile coordinates)

        Returns bitmap object for the tile image.

        Tile coordinates are measured from map top-left.
        """

        raise Exception('You must override Tiles.GetTile()')

    def GetInfo(self, level):
        """Get tile info for a particular level.

        level  the level to get tile info for

        Returns (num_tiles_x, num_tiles_y, ppd_x, ppd_y).

        Note that ppd_? may be meaningless for some tiles, so its
        value will be None.
        """

        raise Exception('You must override Tiles.GetInfo()')

    def Geo2Tile(self, xgeo, ygeo):
        """Convert geo to tile fractional coordinates for level in use.

        xgeo   geo longitude in degrees
        ygeo   geo latitude in degrees

        Note that we assume the point *is* on the map!
        """

        raise Exception('You must override Tiles.Geo2Tile()')

    def Tile2Geo(self, xtile, ytile):
        """Convert tile fractional coordinates to geo for level in use.

        xtile  tile fractional X coordinate
        ytile  tile fractional Y coordinate

        Note that we assume the point *is* on the map!
        """

        raise Exception('You must override Tiles.Tile2Geo()')
