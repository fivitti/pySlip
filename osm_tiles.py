#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A tile source that serves OpenStreetMap tiles from the internet.

Uses pyCacheBack to provide in-memory and on-disk caching.
"""

import os
import glob
import math
import pickle
import threading
import traceback
import urllib2
import Queue
import wx
from wx.lib.embeddedimage import PyEmbeddedImage

import tiles
import pycacheback

# if we don't have log.py, don't crash
try:
    import log
    log = log.Log('pyslip.log', log.Log.DEBUG)
except ImportError:
    def log(*args, **kwargs):
        pass


# tiles stored at <basepath>/<level>/<x>/<y>.png
TilePath = '%d/%d/%d.png'

# the 'pending' tile data
def getPendingImage():
    """Generate 'pending' image from embedded data.
    
    We used to have a separate image file for this, but this is better.
    """

    return PyEmbeddedImage(
      "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"
      "ACAAAAQAgAAAEAAAAoD/JPr6+i5duhSPxwkhXq+3s7Mz9T7nHAHA7zLOOWNsfHw8LS3N6/W2"
      "traGQqFkMtnW1kYIoZT+PwhgJaMv2RPAA5v9lNL29vbi4mKbzfary5dVVXW73Y2NjTt27Ghp"
      "afkyWyCEiIuLi36/v6CgQJKk1R8zxmKxmCzLfX19t27dKi0txaDDo4NSurS01NXVtXv37p+/"
      "/fbwxIR3eHhofLyyuFhRlKtXrzY0NHzhFs6fPy84HI7Ozs7XXnvtc7/0PT09x44dI4QMDw/f"
      "vHnzC48DOETAA+b1enfu3EkI+f53v3tvbESipMyd53K5Lly4sHXr1i+zhTfffFN84YUXFEX5"
      "8MMPTSZTRkaG0Wi8du3a5cuXz507d/v27YmJCZfL5fF4uru7x8bGamtrZ2ZmmpubI5FIfn7+"
      "kSNHenp6Wltbq6urrVYrdgk8GPF4/MyZM3fuDJ15t6W7u/vK9Qvf+t42h9N25eKVf3z/F+FE"
      "UIvRjo6Ourq6EydOlJSUNDc3V1VVtbW1Wa3Wo0ePbty4sbe3t7m5eXR0VBwYGOjt7X355Zfb"
      "2tomJiacTufhw4effvppWZYDgcCzzz4bDodbW1t3797d0tJSVVV18ODBioqK06dPr1279uTJ"
      "k8vLy2az2e/3b9iwATsGHlgA165dU6XFdd8oN1jFkvICQohOJzvzHO4CV7ZT8fR7v1G/sbi4"
      "+JVXXlFV9d13301PTz937tzzzz9/6dKlCxcutLe379u3r6OjQ/rJT35itVr1er3dbj906FBP"
      "T09jY+O2bdvS0tI8Hs+mTZvee++9pqamvXv3njp16uOPP7ZarQcPHhwbG/N6vZzzQ4cOffDB"
      "B6lFKIAHw2w2r6mu8EdGBSpYLGZCCCecEGI2m1JfULLtlRVrCCF5eXnt7e2ZmZnt7e319fWy"
      "LLvd7paWlgMHDqxbty4ajQp2u12v1xNCCgsL6+vrBwcH9+/fn7pEiMfjnPN4PG6xWAghdrtd"
      "UZRwOHzixInR0dHNmzcLgmCxWKxW68LCAvYKPEiyTkrN+1AovBBc4pyHQ5GVT1MzkxBSXV1t"
      "MBj2798/MjLS1NR06tSpGzduvPrqq++8887169c1TRMPHDiw8tcuXrxYV1e3a9cuQojRaMzK"
      "yiosLHQ4HJWVlXa7PS8vr7a2dvv27X6//7nnnisvL1cUpbS01OVypaen5+XlYa/AA+PzzyxG"
      "ZhljgdngrG/eZrd03+h35jkkUSSEJCLClsZtqZ/12trazZs3W63WLVu2WK3WZ555prKysqGh"
      "wW63b9++nV6+fDl1y2BmZubFF188ffq02WxevbaT+nTlxb+zCvQlbz0AfH3hUOStljcys9NW"
      "3kkkVFnWEULueEdf+qNXFEVJvc8Y0zRNEATG2GcHEFlOvZBWZq3RaHzppZfMZvPqqfybL34b"
      "zH54kGLxqBbW9dztL6rMt9ushBBZ1jHOxu/c21j7pKIoqWmsadr7Fy4tLCwNDA5LokAoIYRE"
      "o/G//ovD9wNY2aLNZmtqasJUhsfCxMSEyWR6svDJjFzXP7W3BcNzAiGMc5kahRphZRpzzjMy"
      "MvLcuZ7BO4IoEEIooaIormxHwlDC46impqa/u3vr7t02my3LkX28+Y21dZWJZCK++Ft/vilJ"
      "JfGvbtpKPV3XNKa580uznbiKhcfGyMiI3W632WyEkHA4LEnSQnDJ4xkrL6t44oknVi8HpQ4F"
      "92c/4TpZcGVaen59jXBCCJH8vvFkMpmhZGFM4XHBOb/d27s4P5/6z/7+fmeuY2Y6IOt1Fpsl"
      "qar/fP59URQJJYmENhOKllVWpG4UUEJFge/5vW+Nj3iWI0uU0v8LFBxSmlO0UKUAAAAASUVO"
      "RK5CYII=").GetImage()


# the 'error' tile data
def getErrorImage():
    """Generate 'error' image from embedded data.
    
    We used to have a separate image file for this, but this is better.
    """

    return PyEmbeddedImage(
    "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").GetImage()


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
        tile_path = os.path.join(self._tiles_dir, TilePath % key)
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

        tile_path = os.path.join(self._tiles_dir, TilePath % key)
        dir_path = os.path.dirname(tile_path)
        try:
            os.makedirs(dir_path)
        except OSError:
            # we assume it's a "directory exists' error, which we ignore
            pass
        value.SaveFile(tile_path, wx.BITMAP_TYPE_JPEG)

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
            (level, x, y) = self.requests.get()

            try:
                tile_url = self.server + self.tilepath % (level, x, y)
                f = urllib2.urlopen(urllib2.Request(tile_url))
                if f.info().getheader('Content-Type') == 'image/jpeg':
                    image = wx.ImageFromStream(f, wx.BITMAP_TYPE_JPEG)
                else:
                    # tile not available!
                    image = self.error_tile_image
                wx.CallAfter(self.callafter, level, x, y, image)
            except urllib2.HTTPError, e:
                log('ERROR getting tile %d,%d,%d from %s\n%s'
                    % (level, x, y, tile_url, str(e)))

            self.requests.task_done()

################################################################################
# Class for OSM tiles.   Builds on tiles.Tiles.
################################################################################

# where earlier-cached tiles will be
# this can be overridden in the OSMTiles() constructor
DefaultTilesDir = 'osm_tiles'

# set maximum number of in-memory tiles for each level
DefaultMaxLRU = 10000

class OSMTiles(tiles.Tiles):
    """An object to source OSM tiles for pySlip."""

    TileSize = 256      # width/height of tiles

    # the pool of tile servers used and tile path on server
    # to each tile, %params are (level, x, y)
# OSM tiles
    TileServers = ['http://otile1.mqcdn.com',
                   'http://otile2.mqcdn.com',
                   'http://otile3.mqcdn.com',
                   'http://otile4.mqcdn.com']
    TileURLPath = '/tiles/1.0.0/osm/%d/%d/%d.jpg'
    TileLevels = range(17)
# satellite tiles
#    TileServers = ['http://oatile1.mqcdn.com',
#                   'http://oatile2.mqcdn.com',
#                   'http://oatile3.mqcdn.com',
#                   'http://oatile4.mqcdn.com']
#    TileURLPath = '/tiles/1.0.0/sat/%d/%d/%d.jpg'
#    TileLevels = range(13)         # [0, ..., 12] for the satellite tiles

    # maximum pending requests for each tile server
    MaxServerRequests = 2

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
            tile_levels = self.TileLevels
        self.levels = tile_levels
        self.level = None

        # set min and max tile levels
        self.min_level = min(self.levels)
        self.max_level = max(self.levels)

        # save the CallAfter() function
        self.callback = callback

        # tiles extent for OSM tile data (left, right, top, bottom)
        self.extent = (-180.0, 180.0, -85.0511, 85.0511)

        # prepare tile cache if not already there
        if not os.path.isdir(tiles_dir):
            if os.path.isfile(tiles_dir):
                msg = ("%s doesn't appear to be a tile cache directory"
                       % tiles_dir)
                raise Exception(msg)
            os.makedirs(tiles_dir)
        for level in self.TileLevels:
            level_dir = os.path.join(tiles_dir, '%d' % level)
            if not os.path.isdir(level_dir):
                os.makedirs(level_dir)

        # setup the tile cache (note, no callback set since net unused)
        self.cache = OSMCache(tiles_dir=self.tiles_dir, max_lru=DefaultMaxLRU)

        # set the list of queued unsatisfied requests to 'empty'
        self.queued_requests = {}

        # OSM tiles always (256, 256)
        self.tile_size_x = self.TileSize
        self.tile_size_y = self.TileSize

        # prepare the "pending" and "error" images
        if pending_file:
            self.pending_tile_image = wx.Image(pending_file, wx.BITMAP_TYPE_ANY)
        else:
            self.pending_tile_image = getPendingImage()
        self.pending_tile = self.pending_tile_image.ConvertToBitmap()

        if error_file:
            self.error_tile_image = wx.Image(error_file, wx.BITMAP_TYPE_ANY)
        else:
            self.error_tile_image = getErrorImage()
        self.error_tile = self.error_tile_image.ConvertToBitmap()

        # test for firewall - use proxy (if supplied)
        test_url = self.TileServers[0] + self.TileURLPath % (0, 0, 0)
        try:
            urllib2.urlopen(test_url)
        except:
            log('Error doing simple connection to: %s' % test_url)
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
        for server in self.TileServers:
            for num_threads in range(self.MaxServerRequests):
                worker = TileWorker(server, self.TileURLPath,
                                    self.request_queue, self._tile_available,
                                    self.error_tile_image)
                self.workers.append(worker)
                worker.start()

    def UseLevel(self, level):
        """Prepare to serve tiles from the required level.

        level  the required level
        """

        if level not in self.levels:
            return None
        self.level = level

        # get tile info
        info = self.GetInfo(level)
        if info is None:            # level doesn't exist
            return None
        (self.num_tiles_x, self.num_tiles_y, self.ppd_x, self.ppd_y) = info

#        # store partial path to level dir (small speedup)
#        self.tile_level_dir = os.path.join(self.tiles_dir, '%d' % level)

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

    def _tile_available(self, level, x, y, image):
        """A tile is available.

        level  level for the tile
        x      x coordinate of tile
        y      y coordinate of tile
        image  tile image data
        """

        # convert image to bitmap, save in cache
        bitmap = image.ConvertToBitmap()

#        image.SaveFile('osm_%d_%d_%d.jpg' % (level, x, y), wx.BITMAP_TYPE_JPEG)
        
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

    def Geo2Tile(self, xgeo, ygeo):
        """Convert geo to tile fractional coordinates for level in use.

        xgeo   geo longitude in degrees
        ygeo   geo latitude in degrees

        Note that we assume the point *is* on the map!

        Code taken from [http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames]
        """

        lat_rad = math.radians(ygeo)
        n = 2.0 ** self.level
        xtile = (xgeo + 180.0) / 360.0 * n
        ytile = ((1.0 - math.log(math.tan(lat_rad) + (1.0/math.cos(lat_rad))) / math.pi) / 2.0) * n

        return (xtile, ytile)

    def Tile2Geo(self, xtile, ytile):
        """Convert tile fractional coordinates to geo for level in use.

        xtile  tile fractional X coordinate
        ytile  tile fractional Y coordinate

        Note that we assume the point *is* on the map!

        Code taken from [http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames]
        """

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
            (lon, lat) = tiles.Tile2Geo(tile_x, tile_y)
            msg = 'Expected geo (%f,%f) but got (%f,%f)' % (expect_lon, expect_lat, lon, lat)
            self.assertAlmostEqual(expect_lon, lon, places=3, msg=msg)
            self.assertAlmostEqual(expect_lat, lat, places=3, msg=msg)

            # check lon/lat of bottom left corner of map
            expect_lon = min_lon
            expect_lat = min_lat
            tile_x = 0.0
            tile_y = tiles.num_tiles_y
            (lon, lat) = tiles.Tile2Geo(tile_x, tile_y)
            msg = 'Expected geo (%f,%f) but got (%f,%f)' % (expect_lon, expect_lat, lon, lat)
            self.assertAlmostEqual(expect_lon, lon, places=3, msg=msg)
            self.assertAlmostEqual(expect_lat, lat, places=3, msg=msg)

            # check lon/lat of top right corner of map
            expect_lon = max_lon
            expect_lat = max_lat
            tile_x = tiles.num_tiles_x
            tile_y = 0.0
            (lon, lat) = tiles.Tile2Geo(tile_x, tile_y)
            msg = 'Expected geo (%f,%f) but got (%f,%f)' % (expect_lon, expect_lat, lon, lat)
            self.assertAlmostEqual(expect_lon, lon, places=3, msg=msg)
            self.assertAlmostEqual(expect_lat, lat, places=3, msg=msg)

            # check lon/lat of bottom right corner of map
            expect_lon = max_lon
            expect_lat = min_lat
            tile_x = tiles.num_tiles_x
            tile_y = tiles.num_tiles_y
            (lon, lat) = tiles.Tile2Geo(tile_x, tile_y)
            msg = 'Expected geo (%f,%f) but got (%f,%f)' % (expect_lon, expect_lat, lon, lat)
            self.assertAlmostEqual(expect_lon, lon, places=3, msg=msg)
            self.assertAlmostEqual(expect_lat, lat, places=3, msg=msg)

            # check lon/lat of middle of map
            expect_lon = min_lon + (max_lon - min_lon)/2.0
            expect_lat = 0.0
            tile_x = tiles.num_tiles_x / 2.0
            tile_y = tiles.num_tiles_y / 2.0
            (lon, lat) = tiles.Tile2Geo(tile_x, tile_y)
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
            (xtile, ytile) = tiles.Geo2Tile(geo_x, geo_y)
            msg = ('Expected tile (%f,%f) but got (%f,%f)'
                   % (expect_xtile, expect_ytile, xtile, ytile))
            self.assertAlmostEqual(expect_xtile, xtile, places=3, msg=msg)
            self.assertAlmostEqual(expect_ytile, ytile, places=3, msg=msg)

            # calculate where (.num_tiles_x,0)(Tile) should be in geo coords, check
            expect_xtile = tiles.num_tiles_x
            expect_ytile = 0.0
            geo_x = max_lon
            geo_y = max_lat
            (xtile, ytile) = tiles.Geo2Tile(geo_x, geo_y)
            msg = ('Expected tile (%f,%f) but got (%f,%f)'
                   % (expect_xtile, expect_ytile, xtile, ytile))
            self.assertAlmostEqual(expect_xtile, xtile, places=3, msg=msg)
            self.assertAlmostEqual(expect_ytile, ytile, places=3, msg=msg)

            # calculate where (0,.num_tiles_x)(Tile) should be in geo coords, check
            expect_xtile = 0.0
            expect_ytile = tiles.num_tiles_y
            geo_x = min_lon
            geo_y = min_lat
            (xtile, ytile) = tiles.Geo2Tile(geo_x, geo_y)
            msg = ('Expected tile (%f,%f) but got (%f,%f)'
                   % (expect_xtile, expect_ytile, xtile, ytile))
            self.assertAlmostEqual(expect_xtile, xtile, places=3, msg=msg)
            self.assertAlmostEqual(expect_ytile, ytile, places=3, msg=msg)

            # calculate where (.num_tiles_x,.num_tiles_x)(Tile) should be in geo coords, check
            expect_xtile = tiles.num_tiles_x
            expect_ytile = tiles.num_tiles_y
            geo_x = max_lon
            geo_y = min_lat
            (xtile, ytile) = tiles.Geo2Tile(geo_x, geo_y)
            msg = ('Expected tile (%f,%f) but got (%f,%f)'
                   % (expect_xtile, expect_ytile, xtile, ytile))
            self.assertAlmostEqual(expect_xtile, xtile, places=3, msg=msg)
            self.assertAlmostEqual(expect_ytile, ytile, places=3, msg=msg)

            # calculate where (.num_tiles_x/2,.num_tiles_x/2)(Tile) should be in geo coords, check
            expect_xtile = tiles.num_tiles_x/2.0
            expect_ytile = tiles.num_tiles_y/2.0
            geo_x = min_lon + (max_lon-min_lon)/2.0
            geo_y = min_lat + (max_lat-min_lat)/2.0
            (xtile, ytile) = tiles.Geo2Tile(geo_x, geo_y)
            msg = ('Expected tile (%f,%f) but got (%f,%f)'
                   % (expect_xtile, expect_ytile, xtile, ytile))
            self.assertAlmostEqual(expect_xtile, xtile, places=3, msg=msg)
            self.assertAlmostEqual(expect_ytile, ytile, places=3, msg=msg)

    app = wx.App()
    app_frame = AppFrame()
    app_frame.Show()
    app.MainLoop()

