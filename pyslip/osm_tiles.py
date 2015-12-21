#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A tile source that serves OpenStreetMap tiles from the internet.

Uses pyCacheBack to provide in-memory and on-disk caching.
"""

import os
import glob
import math
import threading
import traceback
import urllib2
import Queue
import wx

import tiles
import pycacheback
import error_pending_tiles as ept


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
# Change values below here to configure an internet tile source.
###############################################################################

# attributes used for tileset introspection
# names must be unique amongst tile modules
TilesetName = 'OpenStreetMap Tiles'
TilesetShortName = 'OSM Tiles'
TilesetVersion = '1.0'

# the pool of tile servers used
TileServers = ['http://otile1.mqcdn.com',
               'http://otile2.mqcdn.com',
               'http://otile3.mqcdn.com',
               'http://otile4.mqcdn.com',
              ]

# the path on the server to a tile
# {} params are Z=level, X=column, Y=row, origin at map top-left
TileURLPath = '/tiles/1.0.0/osm/{Z}/{X}/{Y}.jpg'

# tile levels to be used
TileLevels = range(17)

# maximum pending requests for each tile server
MaxServerRequests = 2

# set maximum number of in-memory tiles for each level
DefaultMaxLRU = 10000

# size of tiles
TileWidth = 256
TileHeight = 256

# where earlier-cached tiles will be
# this can be overridden in the __init__ method
DefaultTilesDir = 'osm_tiles'

###############################################################################
# End of configuration.  You should not need to change anything below here.
###############################################################################

# figure out tile filename extension from TileURLPath
TileExtension = os.path.splitext(TileURLPath)[1][1:]
TileExtensionLower = TileExtension.lower()      # ensure lower case

# tiles stored on disk at <DefaultTilesDir>/<TilePath>
TilePath = '{Z}/{X}/{Y}.%s' % TileExtensionLower

# allowed file types and associated values
AllowedFileTypes = {'jpg': wx.BITMAP_TYPE_JPEG,
                    'png': wx.BITMAP_TYPE_PNG,
                   }

#####
# Figure out various constants used in the program
#####

# determine the file bitmap type
try:
    BitmapFileType = AllowedFileTypes[TileExtensionLower]
except KeyError as e:
    raise TypeError("Bad TileExtension value, got '%s', expected one of %s"
                    % (str(TileExtension), str(AllowedFileTypes.keys())))

# compose the expected 'Content-Type' string on request result
# if we get here we know the extension is a valid value
if TileExtensionLower == 'jpg':
    ContentType = 'image/jpeg'
elif TileExtensionLower == 'png':
    ContentType = 'image/png'


######
# Override the pyCacheBack object to handle OSM tile retrieval
######

class OSMCache(pycacheback.pyCacheBack):

    def _get_from_back(self, key):
        """Retrieve value for 'key' from backing storage.

        key  tuple (level, x, y)
             where level is the level of the tile
                   x, y  is the tile coordinates (integer)

        Raises KeyError if tile not found.
        """

        # look for item in disk cache
        (level, x, y) = key
        tile_path = os.path.join(self._tiles_dir, TilePath.format(Z=level, X=x, Y=y))
        if not os.path.exists(tile_path):
            # tile not there, raise KeyError
            raise KeyError

        # we have the tile file - read into memory, cache it & return
        image = wx.Image(tile_path, wx.BITMAP_TYPE_ANY)
        bitmap = image.ConvertToBitmap()
        return bitmap

    def _put_to_back(self, key, value):
        """Put a bitmap into on-disk cache.

        value  the wx.Image to save
        key     a tuple: (level, x, y)
                where level  level for bitmap
                      x      integer tile coordinate
                      y      integer tile coordinate
        """

        (level, x, y) = key
        tile_path = os.path.join(self._tiles_dir, TilePath.format(Z=level, X=x, Y=y))
        dir_path = os.path.dirname(tile_path)
        try:
            os.makedirs(dir_path)
        except OSError:
            # we assume it's a "directory exists' error, which we ignore
            pass
        value.SaveFile(tile_path, BitmapFileType)

################################################################################
# Worker class for internet tile retrieval
################################################################################

class TileWorker(threading.Thread):
    """Thread class that gets request from queue, loads tile, calls callback."""

    def __init__(self, server, tilepath, requests, callafter, error_tile):
        """Prepare the tile worker.

        server     server URL
        tilepath   path to tile on server
        requests   the request queue
        callafter  function to CALL AFTER tile available

        Results are returned in the CallAfter() params.
        """

        threading.Thread.__init__(self)

        self.server = server
        self.tilepath = tilepath
        self.requests = requests
        self.callafter = callafter
        self.error_tile_image = error_tile
        self.daemon = True

    def run(self):
        while True:
            # get zoom level and tile coordinates to retrieve
            (level, x, y) = self.requests.get()

            image = self.error_tile_image
            error = False       # True if we get an error
            try:
                tile_url = self.server + self.tilepath.format(Z=level, X=x, Y=y)
                f = urllib2.urlopen(urllib2.Request(tile_url))
                if f.info().getheader('Content-Type') == ContentType:
                    image = wx.ImageFromStream(f, BitmapFileType)
            except Exception as e:
                error = True
                log('%s exception getting tile %d,%d,%d from %s\n%s'
                    % (type(e).__name__, level, x, y, tile_url, e.message))

            wx.CallAfter(self.callafter, level, x, y, image, error)
            self.requests.task_done()

################################################################################
# Class for OSM tiles.   Builds on tiles.Tiles.
################################################################################

class OSMTiles(tiles.Tiles):
    """An object to source OSM tiles for pySlip."""

    def __init__(self, tiles_dir=None, tile_levels=None, callback=None,
                 http_proxy=None, pending_file=None, error_file=None):
        """Override the base class for local tiles.

        tiles_dir     tile cache directory, may contain tiles
        tile_levels   list of tile levels to be served
        callback      caller function to call on tile available
        http_proxy    HTTP proxy to use if there is a firewall
        pending_file  path to picture file for the 'pending' tile
        error_file    path to picture file for the 'error' tile
        """

        # check tiles_dir & tile_levels
        if tiles_dir is None:
            tiles_dir = DefaultTilesDir
        self.tiles_dir = tiles_dir

        if tile_levels is None:
            tile_levels = TileLevels
        self.levels = tile_levels
        self.level = None

        # set min and max tile levels
        self.min_level = min(self.levels)
        self.max_level = max(self.levels)

        # save the CallAfter() function
        self.available_callback = callback

        # tiles extent for OSM tile data (left, right, top, bottom)
        self.extent = (-180.0, 180.0, -85.0511, 85.0511)

        # prepare tile cache if not already there
        if not os.path.isdir(tiles_dir):
            if os.path.isfile(tiles_dir):
                msg = ("%s doesn't appear to be a tile cache directory"
                       % tiles_dir)
                raise Exception(msg)
            os.makedirs(tiles_dir)
        for level in self.levels:
            level_dir = os.path.join(tiles_dir, '%d' % level)
            if not os.path.isdir(level_dir):
                os.makedirs(level_dir)

        # setup the tile cache (note, no callback set since net unused)
        self.cache = OSMCache(tiles_dir=self.tiles_dir, max_lru=DefaultMaxLRU)

        # set the list of queued unsatisfied requests to 'empty'
        self.queued_requests = {}

        # set tile size
        self.tile_size_x = TileWidth
        self.tile_size_y = TileHeight

        # prepare the "pending" and "error" images
        if pending_file:
            self.pending_tile_image = wx.Image(pending_file, wx.BITMAP_TYPE_ANY)
        else:
            self.pending_tile_image = ept.getPendingImage()
        self.pending_tile = self.pending_tile_image.ConvertToBitmap()

        if error_file:
            self.error_tile_image = wx.Image(error_file, wx.BITMAP_TYPE_ANY)
        else:
            self.error_tile_image = ept.getErrorImage()
        self.error_tile = self.error_tile_image.ConvertToBitmap()

        # test for firewall - use proxy (if supplied)
        test_url = TileServers[0] + TileURLPath.format(Z=0, X=0, Y=0)
        try:
            urllib2.urlopen(test_url)
        except Exception as e:
            log('%s exception doing simple connection to: %s'
                % (type(e).__name__, test_url))
            log(''.join(traceback.format_exc()))

            if http_proxy:
                proxy = urllib2.ProxyHandler({'http': http_proxy})
                opener = urllib2.build_opener(proxy)
                urllib2.install_opener(opener)
                try:
                    urllib2.urlopen(test_url)
                except:
                    msg = ("Using HTTP proxy %s, "
                           "but still can't get through a firewall!")
                    raise Exception(msg)
            else:
                msg = ("There is a firewall but you didn't "
                       "give me an HTTP proxy to get through it?")
                raise Exception(msg)

        # set up the request queue and worker threads
        self.request_queue = Queue.Queue()  # entries are (level, x, y)
        self.workers = []
        for server in TileServers:
            for num_threads in range(MaxServerRequests):
                worker = TileWorker(server, TileURLPath,
                                    self.request_queue, self._tile_available,
                                    self.error_tile_image)
                self.workers.append(worker)
                worker.start()

    def SetAvailableCallback(self, callback):
        """Set the "tile now available" callback routine.

        callback  function with signature callback(level, x, y)

        where 'level' is the level of the tile and 'x' and 'y' are
        the coordinates of the tile that is now available.
        """

        self.available_callback = callback

    def UseLevel(self, level):
        """Prepare to serve tiles from the required level.

        level  the required level

        Returns True if zoom was performed, else False.
        """

        # first, CAN we zoom to this level?
        if level not in self.levels:
            return None
        self.level = level

        # get tile info
        info = self.GetInfo(level)
        if info is None:            # level doesn't exist
            return None
        (self.num_tiles_x, self.num_tiles_y, self.ppd_x, self.ppd_y) = info

        # flush any outstanding requests.
        # we do this to speed up multiple-level zooms so the user doesn't
        # sit waiting for tiles to arrive that won't be shown.
        self.FlushRequests()

        # finally, return True
        return True

    def GetInfo(self, level):
        """Get tile info for a particular level.

        level  the level to get tile info for

        Returns (num_tiles_x, num_tiles_y, ppd_x, ppd_y).

        Note that ppd_? may be meaningless for some tiles, so its
        value will be None.
        """

        self.num_tiles_x = int(math.pow(2, self.level))
        self.num_tiles_y = int(math.pow(2, self.level))

        return (self.num_tiles_x, self.num_tiles_y, None, None)

    def GetTile(self, x, y):
        """Get bitmap for tile at tile coords (x, y) and current level.

        x  X coord of tile required (tile coordinates)
        y  Y coord of tile required (tile coordinates)

        Returns bitmap object for the tile image.
        Tile coordinates are measured from map top-left.

        We override the existing GetTile() method to add code to retrieve
        tiles from the internet if not in on-disk cache.
        """

        try:
            tile = self.cache[(self.level, x, y)]
        except KeyError:
            # start process of getting tile from 'net, return 'pending' image
            self.GetInternetTile(self.level, x, y)
            tile = self.pending_tile

        return tile

    def GetInternetTile(self, level, x, y):
        """Start the process to get internet tile.

        level, x, y  identify the required tile

        If we don't already have this tile (or getting it), queue a request and
        also put the request into a 'queued request' dictionary.  We
        do this since we can't peek into a Queue to see what's there.
        """

        tile_key = (level, x, y)
        if tile_key not in self.queued_requests:
            # add tile request to the server request queue
            self.request_queue.put(tile_key)
            self.queued_requests[tile_key] = True

    def FlushRequests(self):
        """Delete any outstanding tile requests."""

        self.request_queue.queue.clear()
        self.queued_requests.clear()

    def _tile_available(self, level, x, y, image, error):
        """A tile is available.

        level  level for the tile
        x      x coordinate of tile
        y      y coordinate of tile
        image  tile image data
        error  True if image is 'error' image
        """

        # convert image to bitmap, save in cache
        bitmap = image.ConvertToBitmap()

        # don't cache error images, maybe we can get it again later
        if not error:
            self._cache_tile(image, bitmap, level, x, y)

        # remove the request from the queued requests
        # note that it may not be there - a level change can flush the dict
        try:
            del self.queued_requests[(level, x, y)]
        except KeyError:
            pass

        # tell the world a new tile is available
        wx.CallAfter(self.available_callback, level, x, y, image, bitmap)

    def _cache_tile(self, image, bitmap, level, x, y):
        """Save a tile update from the internet.

        image   wxPython image
        bitmap  bitmap of the image
        level   zoom level
        x       tile X coordinate
        y       tile Y coordinate

        We may already have a tile at (level, x, y).  Update in-memory cache
        and on-disk cache with this new one.
        """

        self.cache[(level, x, y)] = bitmap
        self.cache._put_to_back((level, x, y), image)

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

        tile  a tupl;e (xtile,ytile) of tile fractional coordinates

        Note that we assume the point *is* on the map!

        Code taken from [http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames]
        """

        (xtile, ytile) = tile
        n = 2.0 ** self.level
        xgeo = xtile / n * 360.0 - 180.0
        yrad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
        ygeo = math.degrees(yrad)

        return (xgeo, ygeo)


if __name__ == '__main__':
    import unittest

    DefaultAppSize = (512, 512)
    DemoName = 'OSM Tiles Test'
    DemoVersion = '0.1'


    # we need a WX app running for the test code to work
    class AppFrame(wx.Frame):

        def __init__(self):
            wx.Frame.__init__(self, None, size=DefaultAppSize,
                              title='%s %s' % (DemoName, DemoVersion))
            self.SetMinSize(DefaultAppSize)
            self.panel = wx.Panel(self, wx.ID_ANY)
            self.panel.SetBackgroundColour(wx.WHITE)
            self.panel.ClearBackground()
            self.Bind(wx.EVT_CLOSE, self.onClose)

            unittest.main()

        def onClose(self, event):
            import time
            time.sleep(10)
            self.Destroy()


    class TestOSMTiles(unittest.TestCase):

        def test_Tile2Geo(self):
            """Exercise tiles.Tile2Geo() at various known places."""

            tiles = OSMTiles(tiles_dir=DefaultTilesDir)
            tiles.UseLevel(2)
            (min_lon, max_lon, min_lat, max_lat) = tiles.extent

            # check lon/lat of top left corner of map
            expect_lon = min_lon
            expect_lat = max_lat
            tile_x = 0.0
            tile_y = 0.0
            (lon, lat) = tiles.Tile2Geo((tile_x, tile_y))
            msg = 'Expected geo (%f,%f) but got (%f,%f)' % (expect_lon, expect_lat, lon, lat)
            self.assertAlmostEqual(expect_lon, lon, places=3, msg=msg)
            self.assertAlmostEqual(expect_lat, lat, places=3, msg=msg)

            # check lon/lat of bottom left corner of map
            expect_lon = min_lon
            expect_lat = min_lat
            tile_x = 0.0
            tile_y = tiles.num_tiles_y
            (lon, lat) = tiles.Tile2Geo((tile_x, tile_y))
            msg = 'Expected geo (%f,%f) but got (%f,%f)' % (expect_lon, expect_lat, lon, lat)
            self.assertAlmostEqual(expect_lon, lon, places=3, msg=msg)
            self.assertAlmostEqual(expect_lat, lat, places=3, msg=msg)

            # check lon/lat of top right corner of map
            expect_lon = max_lon
            expect_lat = max_lat
            tile_x = tiles.num_tiles_x
            tile_y = 0.0
            (lon, lat) = tiles.Tile2Geo((tile_x, tile_y))
            msg = 'Expected geo (%f,%f) but got (%f,%f)' % (expect_lon, expect_lat, lon, lat)
            self.assertAlmostEqual(expect_lon, lon, places=3, msg=msg)
            self.assertAlmostEqual(expect_lat, lat, places=3, msg=msg)

            # check lon/lat of bottom right corner of map
            expect_lon = max_lon
            expect_lat = min_lat
            tile_x = tiles.num_tiles_x
            tile_y = tiles.num_tiles_y
            (lon, lat) = tiles.Tile2Geo((tile_x, tile_y))
            msg = 'Expected geo (%f,%f) but got (%f,%f)' % (expect_lon, expect_lat, lon, lat)
            self.assertAlmostEqual(expect_lon, lon, places=3, msg=msg)
            self.assertAlmostEqual(expect_lat, lat, places=3, msg=msg)

            # check lon/lat of middle of map
            expect_lon = min_lon + (max_lon - min_lon)/2.0
            expect_lat = 0.0
            tile_x = tiles.num_tiles_x / 2.0
            tile_y = tiles.num_tiles_y / 2.0
            (lon, lat) = tiles.Tile2Geo((tile_x, tile_y))
            msg = 'Expected geo (%f,%f) but got (%f,%f)' % (expect_lon, expect_lat, lon, lat)
            self.assertAlmostEqual(expect_lon, lon, places=3, msg=msg)
            self.assertAlmostEqual(expect_lat, lat, places=3, msg=msg)

        def test_Geo2Tile(self):
            """Exercise Geo2Tile() at various known places."""

            tiles = OSMTiles(tiles_dir=DefaultTilesDir)
            tiles.UseLevel(2)
            (min_lon, max_lon, min_lat, max_lat) = tiles.extent

            # calculate where (0,0)(Tile) should be in geo coords, check
            expect_xtile = 0.0
            expect_ytile = 0.0
            geo_x = min_lon
            geo_y = max_lat
            (xtile, ytile) = tiles.Geo2Tile((geo_x, geo_y))
            msg = ('Expected tile (%f,%f) but got (%f,%f)'
                   % (expect_xtile, expect_ytile, xtile, ytile))
            self.assertAlmostEqual(expect_xtile, xtile, places=3, msg=msg)
            self.assertAlmostEqual(expect_ytile, ytile, places=3, msg=msg)

            # calculate where (.num_tiles_x,0)(Tile) should be in geo coords, check
            expect_xtile = tiles.num_tiles_x
            expect_ytile = 0.0
            geo_x = max_lon
            geo_y = max_lat
            (xtile, ytile) = tiles.Geo2Tile((geo_x, geo_y))
            msg = ('Expected tile (%f,%f) but got (%f,%f)'
                   % (expect_xtile, expect_ytile, xtile, ytile))
            self.assertAlmostEqual(expect_xtile, xtile, places=3, msg=msg)
            self.assertAlmostEqual(expect_ytile, ytile, places=3, msg=msg)

            # calculate where (0,.num_tiles_x)(Tile) should be in geo coords, check
            expect_xtile = 0.0
            expect_ytile = tiles.num_tiles_y
            geo_x = min_lon
            geo_y = min_lat
            (xtile, ytile) = tiles.Geo2Tile((geo_x, geo_y))
            msg = ('Expected tile (%f,%f) but got (%f,%f)'
                   % (expect_xtile, expect_ytile, xtile, ytile))
            self.assertAlmostEqual(expect_xtile, xtile, places=3, msg=msg)
            self.assertAlmostEqual(expect_ytile, ytile, places=3, msg=msg)

            # calculate where (.num_tiles_x,.num_tiles_x)(Tile) should be in geo coords, check
            expect_xtile = tiles.num_tiles_x
            expect_ytile = tiles.num_tiles_y
            geo_x = max_lon
            geo_y = min_lat
            (xtile, ytile) = tiles.Geo2Tile((geo_x, geo_y))
            msg = ('Expected tile (%f,%f) but got (%f,%f)'
                   % (expect_xtile, expect_ytile, xtile, ytile))
            self.assertAlmostEqual(expect_xtile, xtile, places=3, msg=msg)
            self.assertAlmostEqual(expect_ytile, ytile, places=3, msg=msg)

            # calculate where (.num_tiles_x/2,.num_tiles_x/2)(Tile) should be in geo coords, check
            expect_xtile = tiles.num_tiles_x/2.0
            expect_ytile = tiles.num_tiles_y/2.0
            geo_x = min_lon + (max_lon-min_lon)/2.0
            geo_y = min_lat + (max_lat-min_lat)/2.0
            (xtile, ytile) = tiles.Geo2Tile((geo_x, geo_y))
            msg = ('Expected tile (%f,%f) but got (%f,%f)'
                   % (expect_xtile, expect_ytile, xtile, ytile))
            self.assertAlmostEqual(expect_xtile, xtile, places=3, msg=msg)
            self.assertAlmostEqual(expect_ytile, ytile, places=3, msg=msg)

    app = wx.App()
    app_frame = AppFrame()
    app_frame.Show()
    app.MainLoop()

