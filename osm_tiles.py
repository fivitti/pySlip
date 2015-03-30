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

# a pale green 256x256 tile for the 'pending' tile
PendingImage = (
      "iVBORw0KGgoAAAANSUhEUgAAAQAAAAEACAIAAADTED8xAAAAAXNSR0IArs4c6QAAAAlwSFlz"
      "AAALEwAACxMBAJqcGAAAAAd0SU1FB9wDDgM1MxHwZu4AAAAZdEVYdENvbW1lbnQAQ3JlYXRl"
      "ZCB3aXRoIEdJTVBXgQ4XAAAB/UlEQVR42u3TQREAAAQAQfQPqwFvGexGuJnLng74qiTAAGAA"
      "MAAYAAwABgADgAHAAGAAMAAYAAwABgADgAHAAGAAMAAYAAwABgADgAHAAGAAMAAYAAwABgAD"
      "gAHAAGAAMAAYAAwABgADgAHAAGAAMAAYAAwABgADgAHAAGAAMAAGAAOAAcAAYAAwABgADAAG"
      "AAOAAcAAYAAwABgADAAGAAOAAcAAYAAwABgADAAGAAOAAcAAYAAwABgADAAGAAOAAcAAYAAw"
      "ABgADAAGAAOAAcAAYAAwABgADAAGAAOAAcAAGAAMAAYAA4ABwABgADAAGAAMAAYAA4ABwABg"
      "ADAAGAAMAAYAA4ABwABgADAAGAAMAAYAA4ABwABgADAAGAAMAAYAA4ABwABgADAAGAAMAAYA"
      "A4ABwABgADAAGAAMAAbAAGAAMAAYAAwABgADgAHAAGAAMAAYAAwABgADgAHAAGAAMAAYAAwA"
      "BgADgAHAAGAAMAAYAAwABgADgAHAAGAAMAAYAAwABgADgAHAAGAAMAAYAAwABgADgAHAAGAA"
      "MAAYAAOAAcAAYAAwABgADAAGAAOAAcAAYAAwABgADAAGAAOAAcAAYAAwABgADAAGAAOAAcAA"
      "YAAwABgADAAGAAOAAcAAYAAwABgADAAGAAOAAcAAYAAwABgADAAGgGsBiN4E31uv8wcAAAAA"
      "SUVORK5CYII=")

# a pale red 256x256 tile for the 'error' tile
ErrorImage = (
      "iVBORw0KGgoAAAANSUhEUgAAAQAAAAEACAIAAADTED8xAAAAAXNSR0IArs4c6QAAAAlwSFlz"
      "AAALEwAACxMBAJqcGAAAAAd0SU1FB9wDDgM1KJuVrwIAAAAZdEVYdENvbW1lbnQAQ3JlYXRl"
      "ZCB3aXRoIEdJTVBXgQ4XAAAB/UlEQVR42u3TQREAAAQAQfQPqwFvGexGuJnL6Q74qiTAAGAA"
      "MAAYAAwABgADgAHAAGAAMAAYAAwABgADgAHAAGAAMAAYAAwABgADgAHAAGAAMAAYAAwABgAD"
      "gAHAAGAAMAAYAAwABgADgAHAAGAAMAAYAAwABgADgAHAAGAAMAAGAAOAAcAAYAAwABgADAAG"
      "AAOAAcAAYAAwABgADAAGAAOAAcAAYAAwABgADAAGAAOAAcAAYAAwABgADAAGAAOAAcAAYAAw"
      "ABgADAAGAAOAAcAAYAAwABgADAAGAAOAAcAAGAAMAAYAA4ABwABgADAAGAAMAAYAA4ABwABg"
      "ADAAGAAMAAYAA4ABwABgADAAGAAMAAYAA4ABwABgADAAGAAMAAYAA4ABwABgADAAGAAMAAYA"
      "A4ABwABgADAAGAAMAAbAAGAAMAAYAAwABgADgAHAAGAAMAAYAAwABgADgAHAAGAAMAAYAAwA"
      "BgADgAHAAGAAMAAYAAwABgADgAHAAGAAMAAYAAwABgADgAHAAGAAMAAYAAwABgADgAHAAGAA"
      "MAAYAAOAAcAAYAAwABgADAAGAAOAAcAAYAAwABgADAAGAAOAAcAAYAAwABgADAAGAAOAAcAA"
      "YAAwABgADAAGAAOAAcAAYAAwABgADAAGAAOAAcAAYAAwABgADAAGgGsBiO0E3x03cI8AAAAA"
      "SUVORK5CYII=")

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

    def _put_to_back(self, image, level, x, y):
        """Put a bitmap into on-disk cache.

        image  the wx.Image to save
        key    a tuple: (level, x, y)
               where level  level for bitmap
                     x      integer tile coordinate
                     y      integer tile coordinate
        """

        tile_path = os.path.join(self._tiles_dir, TilePath % key)
        image.SaveFile(tile_path, wx.BITMAP_TYPE_JPEG)

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
                image.SaveFile('osm_%d_%d_%d.jpg' % (level, x, y), wx.BITMAP_TYPE_JPEG)
                wx.CallAfter(self.callafter, level, x, y, image)
            except urllib2.HTTPError, e:
                log('ERROR getting tile %d,%d,%d from %s\n%s'
                    % (level, x, y, tile_url, str(e)))
                pass

            self.requests.task_done()

######
# Class for OSM tiles.   Builds on tiles.Tiles.
######

# where earlier-cached tiles will be
# this can be overridden in the OSMTiles() constructor
DefaultTilesDir = 'tiles'

# set maximum number of in-memory tiles for each level
DefaultMaxLRU = 10000

class OSMTiles(tiles.Tiles):
    """An object to source OSM tiles for pyslip."""

    TileSize = 256      # width/height of tiles

    # the pool of tile servers used and tile path on server
    # to each tile, %params are (level, x, y)
# OSM tiles
    TileServers = ['http://otile1.mqcdn.com',
                   'http://otile2.mqcdn.com',
                   'http://otile3.mqcdn.com',
                   'http://otile4.mqcdn.com']
    TileURLPath = '/tiles/1.0.0/osm/%d/%d/%d.jpg'
# satellite tiles
#    TileServers = ['http://oatile1.mqcdn.com',
#                   'http://oatile2.mqcdn.com',
#                   'http://oatile3.mqcdn.com',
#                   'http://oatile4.mqcdn.com']
#    TileURLPath = '/tiles/1.0.0/sat/%d/%d/%d.jpg'

    # maximum pending requests for each tile server
    MaxServerRequests = 2

    # available tile levels in MQ_OSM [0, ..., 16]
    # note: some tiles in levels 13+ don't exist
# OSM tiles
    TileLevels = range(17)
# satellite tiles
#    TileLevels = range(13)         # [0, ..., 12] for the satellite tiles

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

        # first, initialize with base code
#        Tiles.__init__(self, tiles_dir, tile_levels)

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
            self.pending_tile = self.pending_tile_image.ConvertToBitmap()
        else:
            self.pending_tile_image = PyEmbeddedImage(PendingImage)
            self.pending_tile = self.pending_tile_image.GetBitmap()

        if error_file:
            self.error_tile_image = wx.Image(error_file, wx.BITMAP_TYPE_ANY)
            self.error_tile = self.error_tile_image.ConvertToBitmap()
        else:
            self.error_tile_image = PyEmbeddedImage(ErrorImage)
            self.error_tile = self.error_tile_image.GetBitmap()

        # test for firewall - use proxy (if supplied)
        test_url = self.TileServers[0] + self.TileURLPath % (0, 0, 0)
        try:
            urllib2.urlopen(test_url)
        except:
            log('Error doing simple connection to: %s' % test_url)
            log(''.join(traceback.format_exc()))

            if http_proxy:
                log('Try using proxy: %s' % str(http_proxy))
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

        # store partial path to level dir (small speedup)
        self.tile_level_dir = os.path.join(self.tiles_dir, '%d' % level)

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
        self._cache_tile(image, bitmap, level, x, y)

        # remove the request from the queued requests
        # note that it may not be there - a level change can flush the dict
        try:
            del self.queued_requests[(level, x, y)]
        except KeyError:
            log('deleting non-existant queued request: %d,%d,%d'
                % (level, x, y))
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
        self.cache._put_to_back(image, level, x, y)

    def Geo2Tile(self, ygeo, xgeo):
        """Convert geo to tile fractional coordinates for level in use.

        ygeo   geo latitude in degrees
        xgeo   geo longitude in degrees

        Note that we assume the point *is* on the map!

        Code taken from [http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames]
        """

        lat_rad = math.radians(ygeo)
        n = 2.0 ** self.level
        xtile = (xgeo + 180.0) / 360.0 * n
        ytile = (1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n
        return (xtile, ytile)

    def Tile2Geo(self, ytile, xtile):
        """Convert tile fractional coordinates to geo for level in use.

        ytile  tile fractional Y coordinate
        xtile  tile fractional X coordinate

        Note that we assume the point *is* on the map!

        Code taken from [http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames]
        """

        n = 2.0 ** self.level
        xgeo = xtile / n * 360.0 - 180.0
        yrad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
        ygeo = math.degrees(yrad)
        return (ygeo, xgeo)
