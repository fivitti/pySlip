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
        print('key=%s' % str(key))

        # look for item in disk cache
        tile_dir = os.path.join(self._tiles_dir, '%d' % level)
        tile_path = os.path.join(tile_dir, self.TilePath % (x, y))
        if not os.path.exists(tile_path):
            # tile not there, return None
            print('tile %s not found' % tile_path)
            return None

        print('tile %s FOUND' % tile_path)
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
            raise Exception("'%s' doesn't appear to be a local tile directory"
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
