#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A _base_ Tiles object for pySlip tiles.

All tile sources should inherit from this base class.
See, for example, pyslip_demo.py and pyslip_demo_net.py.
"""

import os
import glob
import wx
import tile_cache


######
# Base class for a tile source - handles access to a source of tiles.
######

class Tiles(object):
    """An object to source tiles for pyslip."""

    def __init__(self, tile_cache_dir, tile_levels=None):
        """Initialise a Tiles instance.

        tile_cache_dir  tile cache directory, may contain tiles
        tile_levels     list of tile levels to be served
        """

        # save the tile cache directory
        self.tile_cache_dir = tile_cache_dir

        # look in tile directory for levels if none supplied
        if tile_levels is None:
            glob_pattern = os.path.join(tile_cache_dir, '[0-9]*')
            tile_levels = []
            for p in glob.glob(glob_pattern):
                filename = int(os.path.basename(p))
                tile_levels.append(filename)
            tile_levels.sort()

        # setup the tile cache
        self.cache = tile_cache.TileCache(tile_cache_dir, tile_levels)

        # save the levels to be served
        self.levels = tile_levels

        # set min and max tile levels
        self.min_level = min(self.levels)
        self.max_level = max(self.levels)

        # this function is called when a pending tile becomes available
        self.available_callback = None

    def SetAvailableCallback(self, callback):
        """Set the "tile now available" callback routine.

        callback  function with signature callback(level, x, y)
                  where 'level' is the level of the tile and 'x' and 'y' are
                  the coordinates of the tile that is now available.
        """

        self.available_callback = callback

    def UseLevel(self, level):
        """Prepare to serve tiles from the required level.

        level  The required level

        Returns a tuple (map_width, map_height, ppd_x, ppd_y) if successful,
        else None.  The width/height values are pixels.  The ppd_? values are
        pixels-per-degree values for the X and Y directions and are valid only
        in a Cartesian coordinate system.
        """

        if level not in self.levels:
            return None

        # get tile info
        info = self.GetInfo(level)
        if info is None:            # level not used
            return None
        (self.num_tiles_x, self.num_tiles_y, self.ppd_x, self.ppd_y) = info

        # set level we are currently serving
        self.level = level

        # store partial path to level dir (small speedup)
        self.tile_level_dir = os.path.join(self.tile_cache_dir, '%d' % level)

        # finally, return new level info
        return (self.tile_size_x * self.num_tiles_x,
                self.tile_size_y * self.num_tiles_y,
                self.ppd_x, self.ppd_y)

    def GetTile(self, x, y):
        """Get bitmap for tile at tile coords (x, y) and current level.

        x  X coord of tile required (tile coordinates)
        y  Y coord of tile required (tile coordinates)

        Returns bitmap object for the tile image.

        Tile coordinates are measured from map top-left.
        """

        return self.cache.GetTile(self.level, x, y)

    def GetInfo(self, level):
        """Get tile info for a particular level.

        level  the level to get tile info for

        Returns (num_tiles_x, num_tiles_y, ppd_x, ppd_y).

        Note that ppd_? may be meaningless for some tiles, so its
        value will be None.
        """

        raise Exception('You must override Tiles.GetInfo()')

    def ConvertGeo2TileCoords(self, lat_deg, lon_deg, zoom,
                              ppd_x=None, ppd_y=None,
                              map_tlat=None, map_blat=None,
                              map_llon=None, map_rlon=None):
        """Convert lon/lat to tile fractional coordinates.

        lat_deg   geo latitude in degrees
        lon_deg   geo longitude in degrees
        zoom      the map 'level'
        ppd_x     the 'pixel per degree' value in the X direction
        ppd_y     the 'pixel per degree' value in the Y direction
        map_tlat  latitude of top edge of map
        map_blat  latitude of bottom edge of map
        map_llon  longitude of left edge of map
        map_rlon  longitude of right edge of map

        Not all of the above arguments need be supplied, depending on
        the type of tiles.

        Note that we assume the point *is* on the map!
        """

        raise Exception('You must override Tiles.ConvertGeo2TileCoords()')

    def ConvertTileCoords2Geo(xtile, ytile, zoom, ppd_x=None, ppd_y=None):
        """Convert tile fractional coordinates to lon/lat.

        xtile  tile fractional X coordinate
        ytile  tile fractional Y coordinate
        zoom   the map 'level'
        ppd_x  the 'pixel per degree' value in the X direction
        ppd_y  the 'pixel per degree' value in the Y direction

        Not all of the above arguments need be supplied, depending on
        the type of tiles.
        """

        raise Exception('You must override Tiles.ConvertView2Geo()')
