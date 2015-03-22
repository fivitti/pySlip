#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A tile source that serves local pre-generated GMT tiles.

Uses pyCacheBack to provide in-memory and on-disk caching.
"""

import os
import glob
import pickle
import wx

import tiles
import pycacheback


######
# Override the pyCacheBack object to handle GMT tile retrieval
######


class GMTCache(pycacheback.pyCacheBack):

    TilePath = '%d/%d.png'

    def _get_from_back(self, key):
        """Retrieve value for 'key' from backing storage.

        key  tuple (level, x, y)
             where level is the level of the tile
                   x, y  is the tile coordinates (integer)

        Raises KeyError if key not in cache.
        """

        # unpack key
        (level, x, y) = key

        # look for item in disk cache
        tile_dir = os.path.join(self._tiles_dir, '%d' % level)
        tile_path = os.path.join(tile_dir, self.TilePath % (x, y))
        if not os.path.exists(tile_path):
            # tile not there, return None
            return None

        # we have the tile file - read into memory, cache & return
        image = wx.Image(tile_path, wx.BITMAP_TYPE_ANY)
        bitmap = image.ConvertToBitmap()
        return bitmap

######
# Class for pre-generated GMT tiles.   Builds on tiles.Tiles.
######

# where earlier-cached tiles will be
# this can be overridden in the GMTTiles() constructor
DefaultTileDir = 'tiles'

# set maximum number of in-memory tiles for each level
DefaultMaxLRU = 10000

class GMTTiles(tiles.Tiles):
    """An object to source tiles local GMT tiles for pyslip."""

    TileInfoFilename = "tile.info"

    def __init__(self, tiles_dir=None, tile_levels=None):
        """Initialise a GMT local tiles instance.

        tiles_dir  tile cache directory, contains GMT tiles
        tile_levels     list of tile levels to be served
        """

        # see if on-disk cache directory is specified
        if tiles_dir is None:
            tiles_dir = DefaultTileDir

        # open top-level GMT info file (it MUST be there!)
        info_file = os.path.join(tiles_dir, self.TileInfoFilename)
        try:
            with open(info_file, 'rb') as fd:
                (self.extent, self.tile_size,
                     self.sea_colour, self.land_colour) = pickle.load(fd)
        except IOError:
            raise IOError("'%s' doesn't appear to be a local tile directory"
                          % tiles_dir)

        self.tiles_dir = tiles_dir
        (self.tile_size_x, self.tile_size_y) = self.tile_size

        # look in tile directory for levels if none supplied
        if tile_levels is None:
            glob_pattern = os.path.join(tiles_dir, '[0-9]*')
            tile_levels = []
            for p in glob.glob(glob_pattern):
                filename = int(os.path.basename(p))
                tile_levels.append(filename)
            tile_levels.sort()

        # save the levels to be served
        self.levels = tile_levels

        # set min and max tile levels
        self.min_level = min(self.levels)
        self.max_level = max(self.levels)

        # setup the tile cache (note, no callback set since net unused)
        self.cache = GMTCache(tiles_dir=self.tiles_dir, max_lru=DefaultMaxLRU)

    def GetInfo(self, level):
        """Get tile info for a particular level.

        level  the level to get tile info for

        Returns (num_tiles_x, num_tiles_y, ppd_x, ppd_y).

        Note that ppd_? may be meaningless for some tiles, so its
        value will be None.
        """

        # see if we can open the tile info file.
        info_file = os.path.join(self.tiles_dir, '%d' % level,
                                 self.TileInfoFilename)
        try:
            with open(info_file, 'rb') as fd:
                info = pickle.load(fd)
        except IOError:
            info = None

        return info

    def Geo2Tile(self, ygeo, xgeo):
        """Convert geo to tile fractional coordinates for level in use.

        ygeo   geo latitude in degrees
        xgeo   geo longitude in degrees

        Note that we assume the point *is* on the map!
        """

        raise Exception('You must override Tiles.Geo2Tile()')

    def Tile2Geo(self, ytile, xtile):
        """Convert tile fractional coordinates to geo for level in use.

        ytile  tile fractional Y coordinate
        xtile  tile fractional X coordinate

        Note that we assume the point *is* on the map!
        """

        raise Exception('You must override Tiles.Tile2Geo()')
