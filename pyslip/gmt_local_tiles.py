#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A tile source that serves OpenStreetMap tiles from the internet.

Uses pyCacheBack to provide in-memory and on-disk caching.
"""

import os
import pickle

import tiles


# if we don't have log.py, don't crash
try:
    from . import log
    log = log.Log('pyslip.log')
except AttributeError:
    # means log already set up
    pass
except ImportError as e:
    # if we don't have log.py, don't crash
    # fake all log(), log.debug(), ... calls
    def logit(*args, **kwargs):
        pass
    log = logit
    log.debug = logit
    log.info = logit
    log.warn = logit
    log.error = logit
    log.critical = logit

###############################################################################
# Change values below here to configure the OSM tile source.
###############################################################################

# attributes used for tileset introspection
# names must be unique amongst tile modules
tileset_name = 'GMT local tiles'
tileset_shortname = 'GMT tiles'
tileset_version = '1.0'

# the pool of tile servers used
TileServers = None

# the path on the server to a tile
# {} params are Z=level, X=column, Y=row, origin at map top-left
TileURLPath = None

# tile levels to be used
TileLevels = range(5)

# maximum pending requests for each tile server
MaxServerRequests = None

# set maximum number of in-memory tiles for each level
MaxLRU = 10000

# size of tiles
TileWidth = 256
TileHeight = 256

# where earlier-cached tiles will be
# this can be overridden in the __init__ method
TilesDir = 'gmt_tiles'

################################################################################
# Class for GMT local tiles.   Builds on tiles.BaseTiles.
################################################################################

class Tiles(tiles.BaseTiles):
    """An object to source GMT tiles for pySlip."""

    TileInfoFilename = "tile.info"

    def __init__(self, http_proxy=None):
        """Override the base class for GMT tiles.

        Basically, just fill in the BaseTiles class with GMT values from above
        and provide the Geo2Tile() and Tile2Geo() methods.
        """

        super(Tiles, self).__init__(TileLevels, TileWidth, TileHeight,
                                    servers=TileServers, url_path=TileURLPath,
                                    max_server_requests=MaxServerRequests,
                                    max_lru=MaxLRU, tiles_dir=TilesDir,
                                    http_proxy=http_proxy)

        # override the tiles.py extent here, the GMT tileset is different
        self.extent=(-65.0, 295.0, -66.66, 66.66)

        # get tile information into instance
        self.level = min(TileLevels)
        (self.num_tiles_x, self.num_tiles_y,
         self.ppd_x, self.ppd_y) = self.GetInfo(self.level)

    def GetInfo(self, level):
        """Get tile info for a particular level.
        Override the tiles.py method.

        level  the level to get tile info for

        Returns (num_tiles_x, num_tiles_y, ppd_x, ppd_y).
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

    def Geo2Tile(self, geo):
        """Convert geo to tile fractional coordinates for level in use.

        geo  a tuple of geo coordinates (xgeo, ygeo)

        Returns (xtile, ytile).

        Note that we assume the point *is* on the map!

        This is an easy transformation as geo coordinates are Cartesian.
        """

        (xgeo, ygeo) = geo

        # get extent information
        (min_xgeo, max_xgeo, min_ygeo, max_ygeo) = self.extent

        # get 'geo-like' coords with origin at top-left
        x = xgeo - min_xgeo
        y = max_ygeo - ygeo

        tdeg_x = self.tile_size_x / self.ppd_x
        tdeg_y = self.tile_size_y / self.ppd_y

        return (x/tdeg_x, y/tdeg_y)

    def Tile2Geo(self, tile):
        """Convert tile fractional coordinates to geo for level in use.

        tile  a tuple (xtile,ytile) of tile fractional coordinates

        Note that we assume the point *is* on the map!

        This is an easy transformation as geo coordinates are Cartesian.
        """

        (xtile, ytile) = tile

        # get extent information
        (min_xgeo, max_xgeo, min_ygeo, max_ygeo) = self.extent

        # compute tile degree sizes and position in the coordinate system
        tdeg_x = self.tile_size_x / self.ppd_x
        tdeg_y = self.tile_size_y / self.ppd_y
        xgeo = xtile*tdeg_x + min_xgeo
        ygeo = max_ygeo - ytile*tdeg_y

        return (xgeo, ygeo)

