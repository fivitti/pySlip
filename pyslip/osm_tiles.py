"""
A tile source that serves OpenStreetMap tiles from server(s).

Uses pyCacheBack to provide in-memory and on-disk caching.
"""

import math
import pyslip.tiles_net as tiles
import pyslip.log as log
try:
    log = log.Log('pyslip.log')
except AttributeError:
    # means log already set up
    pass


###############################################################################
# Change values below here to configure this tile source.
###############################################################################

# attributes used for tileset introspection
# names must be unique amongst tile modules
TilesetName = 'OpenStreetMap Tiles'
TilesetShortName = 'OSM Tiles'
TilesetVersion = '1.0'

# the pool of tile servers used
TileServers = [
# using 'https://' we get "SSL: CERTIFICATE_VERIFY_FAILED" errors
# try to modify get code to use https and no SSL
#               'https://a.tile.openstreetmap.org',
#               'https://b.tile.openstreetmap.org',
#               'https://c.tile.openstreetmap.org',
               'http://a.tile.openstreetmap.org',
               'http://b.tile.openstreetmap.org',
               'http://c.tile.openstreetmap.org',
              ]

# the path on the server to a tile
# {} params are Z=level, X=column, Y=row, origin at map top-left
TileURLPath = '/{Z}/{X}/{Y}.png'

# tile levels to be used
TileLevels = range(17)

# maximum pending requests for each tile server
MaxServerRequests = 2

# set maximum number of in-memory tiles for each level
MaxLRU = 10000

# where earlier-cached tiles will be
# this can be overridden in the __init__ method
TilesDir = 'osm_tiles'


################################################################################
# Class for these tiles.   Builds on tiles.BaseTiles.
################################################################################

class Tiles(tiles.Tiles):
    """An object to source server tiles for pySlipQt."""

    # size of tiles
    TileWidth = 256
    TileHeight = 256

    def __init__(self, tiles_dir=TilesDir, http_proxy=None):
        """Override the base class for these tiles.

        Basically, just fill in the BaseTiles class with values from above
        and provide the Geo2Tile() and Tile2Geo() methods.
        """

        super().__init__(TileLevels,
                         Tiles.TileWidth, Tiles.TileHeight,
                         tiles_dir=tiles_dir,
                         servers=TileServers, url_path=TileURLPath,
                         max_server_requests=MaxServerRequests,
                         max_lru=MaxLRU, http_proxy=http_proxy)

        # get tile information into instance
        self.level = min(TileLevels)
        (self.num_tiles_x, self.num_tiles_y,
                         self.ppd_x, self.ppd_y) = self.GetInfo(self.level)

    def Geo2Tile(self, geo):
        """Convert geo to tile fractional coordinates for level in use.

        geo  tuple of geo coordinates (xgeo, ygeo)

        Note that we assume the point *is* on the map!

        Code taken from [http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames]
        """

        (xgeo, ygeo) = geo
        lat_rad = math.radians(ygeo)
        n = 2.0 ** self.level
        xtile = (xgeo + 180.0) / 360.0 * n
        ytile = ((1.0 - math.log(math.tan(lat_rad) + (1.0/math.cos(lat_rad))) / math.pi) / 2.0) * n

        return (xtile, ytile)

    def Tile2Geo(self, tile):
        """Convert tile fractional coordinates to geo for level in use.

        tile  a tuple (xtile,ytile) of tile fractional coordinates

        Note that we assume the point *is* on the map!

        Code taken from [http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames]
        """

        (xtile, ytile) = tile
        n = 2.0 ** self.level
        xgeo = xtile / n * 360.0 - 180.0
        yrad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
        ygeo = math.degrees(yrad)

        return (xgeo, ygeo)
