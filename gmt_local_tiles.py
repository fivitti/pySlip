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

# if we don't have log.py, don't crash
try:
    import log
    log = log.Log('pyslip.log', log.Log.DEBUG)
except ImportError:
    def log(*args, **kwargs):
        pass


# attributes used for tileset introspection
tileset_name = ''
tileset_shortname = ''
tileset_version = '1.0'


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

    def __init__(self, tiles_dir=DefaultTileDir, tile_levels=None):
        """Initialise a GMT local tiles instance.

        tiles_dir    tile cache directory, contains GMT tiles
        tile_levels  list of tile levels to be served
        """

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

    def SetAvailableCallback(self, callback):
        """Set the "tile now available" callback routine.

        callback  function with signature callback(level, x, y, image, bitmap)

        where 'level' is the level of the tile, 'x' and 'y' are
        the coordinates of the tile and 'image' and 'bitmap' are tile data.

        For GMT tiles we do nothing as they are all local.
        """

        pass

    def UseLevel(self, level):
        """Prepare to serve tiles from the required level.

        level  the required level

        Throws Exception if level not found.
        """

        if level not in self.levels:
            raise Exception("Level '%s' not used" % str(level))
        self.level = level

        # get tile info
        info = self.GetInfo(level)
        if info is None:            # level doesn't exist
            raise Exception("Level '%s' not used" % str(level))
        (self.num_tiles_x, self.num_tiles_y, self.ppd_x, self.ppd_y) = info

        # store partial path to level dir (small speedup)
        self.tile_level_dir = os.path.join(self.tiles_dir, '%d' % level)

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

    def GetTile(self, x, y):
        """Get bitmap for tile at level,x,y.

        x      X coord of tile required (integer, tile coordinates)
        y      Y coord of tile required (integer, tile coordinates)

        Return tile from the local cache, return None if not found.
        """

#        # the tile 'key'
#        tile_key = (x, y)
#
#        try:
#            # if tile in cache, return it from there
#            bitmap = self.cache[level][tile_key]
#            self.lru[level].remove((x, y))      # remove, add at recent end
#            self.lru[level].insert(0, tile_key)
#        except KeyError:
#            # tile *not* in memory cache look in disk cache
#            tile_dir = os.path.join(self.cache_dir, '%d' % level)
#            tile_path = os.path.join(tile_dir, self.TilePath % (x, y))
#            if not os.path.exists(tile_path):
#                # tile not there, return None
#                bitmap = None
#        else:
#            # we have the tile file - read into memory, cache & return
#            image = wx.Image(tile_path, wx.BITMAP_TYPE_ANY)
#            bitmap = image.ConvertToBitmap()
#            self.cache[level][tile_key] = bitmap
#            self.lru[level].insert(0, tile_key)
#
#        # newly cached tile, check if we must drop old cached tiles
#        self._trim_cache(level)
#
#        return bitmap

        return self.cache[(self.level, x, y)]

    def Geo2Tile(self, xgeo, ygeo):
        """Convert geo to tile fractional coordinates for level in use.

        xgeo   geo longitude in degrees
        ygeo   geo latitude in degrees

        Returns (xtile, ytile).

        Note that we assume the point *is* on the map!

        This is an easy transformation as geo coordinates are Cartesian.
        """

        # get extent information
        (min_xgeo, max_xgeo, min_ygeo, max_ygeo) = self.extent

        # get 'geo-like' coords with origin at top-left
        x = xgeo - min_xgeo
        y = max_ygeo - ygeo

        tdeg_x = self.tile_size_x / self.ppd_x
        tdeg_y = self.tile_size_y / self.ppd_y

        return (x/tdeg_x, y/tdeg_y)

    def Tile2Geo(self, xtile, ytile):
        """Convert tile fractional coordinates to geo for level in use.

        xtile  tile fractional X coordinate
        ytile  tile fractional Y coordinate

        Note that we assume the point *is* on the map!

        This is an easy transformation as geo coordinates are Cartesian.
        """

        # get extent information
        (min_xgeo, max_xgeo, min_ygeo, max_ygeo) = self.extent

        # compute tile degree sizes and position in the coordinate system
        tdeg_x = self.tile_size_x / self.ppd_x
        tdeg_y = self.tile_size_y / self.ppd_y
        xgeo = xtile*tdeg_x + min_xgeo
        ygeo = max_ygeo - ytile*tdeg_y

        return (xgeo, ygeo)


if __name__ == '__main__':
    import unittest

    class TestGMTTiles(unittest.TestCase):

        def test_Tile2Geo(self):
            """Exercise tiles.Tile2Geo() at various known places."""

            tiles = GMTTiles(tiles_dir=DefaultTileDir)
            tiles.UseLevel(2)
            (min_lon, max_lon, min_lat, max_lat) = tiles.extent

            # check lon/lat of top left corner of map
            expect_lon = min_lon
            expect_lat = max_lat
            tile_x = 0.0
            tile_y = 0.0
            (lon, lat) = tiles.Tile2Geo(tile_x, tile_y)
            msg = 'Expected geo (%f,%f) but got (%f,%f)' % (expect_lon, expect_lat, lon, lat)
            self.assertAlmostEqual(expect_lon, lon, places=4, msg=msg)
            self.assertAlmostEqual(expect_lat, lat, places=4, msg=msg)

            # check lon/lat of bottom left corner of map
            expect_lon = min_lon
            expect_lat = min_lat
            tile_x = 0.0
            tile_y = tiles.num_tiles_y
            (lon, lat) = tiles.Tile2Geo(tile_x, tile_y)
            msg = 'Expected geo (%f,%f) but got (%f,%f)' % (expect_lon, expect_lat, lon, lat)
            self.assertAlmostEqual(expect_lon, lon, places=4, msg=msg)
            self.assertAlmostEqual(expect_lat, lat, places=4, msg=msg)

            # check lon/lat of top right corner of map
            expect_lon = max_lon
            expect_lat = max_lat
            tile_x = tiles.num_tiles_x
            tile_y = 0.0
            (lon, lat) = tiles.Tile2Geo(tile_x, tile_y)
            msg = 'Expected geo (%f,%f) but got (%f,%f)' % (expect_lon, expect_lat, lon, lat)
            self.assertAlmostEqual(expect_lon, lon, places=4, msg=msg)
            self.assertAlmostEqual(expect_lat, lat, places=4, msg=msg)

            # check lon/lat of bottom right corner of map
            expect_lon = max_lon
            expect_lat = min_lat
            tile_x = tiles.num_tiles_x
            tile_y = tiles.num_tiles_y
            (lon, lat) = tiles.Tile2Geo(tile_x, tile_y)
            msg = 'Expected geo (%f,%f) but got (%f,%f)' % (expect_lon, expect_lat, lon, lat)
            self.assertAlmostEqual(expect_lon, lon, places=4, msg=msg)
            self.assertAlmostEqual(expect_lat, lat, places=4, msg=msg)

            # check lon/lat of middle of map
            expect_lon = min_lon + (max_lon - min_lon)/2.0
            expect_lat = 0.0
            tile_x = tiles.num_tiles_x / 2.0
            tile_y = tiles.num_tiles_y / 2.0
            (lon, lat) = tiles.Tile2Geo(tile_x, tile_y)
            msg = 'Expected geo (%f,%f) but got (%f,%f)' % (expect_lon, expect_lat, lon, lat)
            self.assertAlmostEqual(expect_lon, lon, places=4, msg=msg)
            self.assertAlmostEqual(expect_lat, lat, places=4, msg=msg)

        def test_Geo2Tile(self):
            """Exercise Geo2Tile() at various known places."""

            tiles = GMTTiles(tiles_dir=DefaultTileDir)
            tiles.UseLevel(2)
            (min_lon, max_lon, min_lat, max_lat) = tiles.extent

            # calculate where (0,0)(Tile) should be in geo coords, check
            expect_xtile = 0.0
            expect_ytile = 0.0
            geo_x = min_lon
            geo_y = max_lat
            (xtile, ytile) = tiles.Geo2Tile(geo_x, geo_y)
            msg = ('Expected tile (%f,%f) but got (%f,%f)'
                   % (expect_xtile, expect_ytile, xtile, ytile))
            self.assertAlmostEqual(expect_xtile, xtile, places=4, msg=msg)
            self.assertAlmostEqual(expect_ytile, ytile, places=4, msg=msg)

            # calculate where (.num_tiles_x,0)(Tile) should be in geo coords, check
            expect_xtile = tiles.num_tiles_x
            expect_ytile = 0.0
            geo_x = max_lon
            geo_y = max_lat
            (xtile, ytile) = tiles.Geo2Tile(geo_x, geo_y)
            msg = ('Expected tile (%f,%f) but got (%f,%f)'
                   % (expect_xtile, expect_ytile, xtile, ytile))
            self.assertAlmostEqual(expect_xtile, xtile, places=4, msg=msg)
            self.assertAlmostEqual(expect_ytile, ytile, places=4, msg=msg)

            # calculate where (0,.num_tiles_x)(Tile) should be in geo coords, check
            expect_xtile = 0.0
            expect_ytile = tiles.num_tiles_y
            geo_x = min_lon
            geo_y = min_lat
            (xtile, ytile) = tiles.Geo2Tile(geo_x, geo_y)
            msg = ('Expected tile (%f,%f) but got (%f,%f)'
                   % (expect_xtile, expect_ytile, xtile, ytile))
            self.assertAlmostEqual(expect_xtile, xtile, places=4, msg=msg)
            self.assertAlmostEqual(expect_ytile, ytile, places=4, msg=msg)

            # calculate where (.num_tiles_x,.num_tiles_x)(Tile) should be in geo coords, check
            expect_xtile = tiles.num_tiles_x
            expect_ytile = tiles.num_tiles_y
            geo_x = max_lon
            geo_y = min_lat
            (xtile, ytile) = tiles.Geo2Tile(geo_x, geo_y)
            msg = ('Expected tile (%f,%f) but got (%f,%f)'
                   % (expect_xtile, expect_ytile, xtile, ytile))
            self.assertAlmostEqual(expect_xtile, xtile, places=4, msg=msg)
            self.assertAlmostEqual(expect_ytile, ytile, places=4, msg=msg)

            # calculate where (.num_tiles_x/2,.num_tiles_x/2)(Tile) should be in geo coords, check
            expect_xtile = tiles.num_tiles_x/2.0
            expect_ytile = tiles.num_tiles_y/2.0
            geo_x = min_lon + (max_lon-min_lon)/2.0
            geo_y = min_lat + (max_lat-min_lat)/2.0
            (xtile, ytile) = tiles.Geo2Tile(geo_x, geo_y)
            msg = ('Expected tile (%f,%f) but got (%f,%f)'
                   % (expect_xtile, expect_ytile, xtile, ytile))
            self.assertAlmostEqual(expect_xtile, xtile, places=4, msg=msg)
            self.assertAlmostEqual(expect_ytile, ytile, places=4, msg=msg)

    suite = unittest.makeSuite(TestGMTTiles, 'test')
    runner = unittest.TextTestRunner()
    runner.run(suite)

