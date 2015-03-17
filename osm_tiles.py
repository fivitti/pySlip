#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A tile source that serves OpenStreetMap tiles from the internet.

Uses pyCacheBack to provide in-memory and on-disk caching.
"""

import os
import glob
import pickle
import wx

import tiles
import pycacheback


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
        tile_path = os.path.join(self._tiles_dir, self.TilePath % key)
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

        tile_path = os.path.join(self._tiles_dir, self.TilePath % key)
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
DefaultTileDir = 'tiles'

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

    def __init__(self, tile_cache_dir, tile_levels, callback=None,
                 http_proxy=None, pending_file=None, error_file=None):
        """Override the base class for local tiles.

        tile_cache_dir  tile cache directory, may contain tiles
        tile_levels     list of tile levels to be served
        callback        caller function to call on tile available
        http_proxy      HTTP proxy to use if there is a firewall
        pending_file    path to picture file for the 'pending' tile
        error_file      path to picture file for the 'error' tile
        """

        # first, initialize with base code
        Tiles.__init__(self, tile_cache_dir, tile_levels)

        # save the CallAfter() function
        self.callback = callback

        # tiles extent for OSM tile data (left, right, top, bottom)
        self.extent = (-180.0, 180.0, -85.0511, 85.0511)

        # prepare tile cache if not already there
        self.tile_cache_dir = tile_cache_dir
        if not os.path.isdir(tile_cache_dir):
            if os.path.isfile(tile_cache_dir):
                msg = ("%s doesn't appear to be a tile cache directory"
                       % tile_cache_dir)
                raise Exception(msg)
            os.makedirs(tile_cache_dir)
        for level in self.TileLevels:
            level_dir = os.path.join(tile_cache_dir, '%d' % level)
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
            self.pending_tile_image = PyEmbeddedImage(self.PendingImage)
            self.pending_tile = self.pending_tile_image.GetBitmap()

        if error_file:
            self.error_tile_image = wx.Image(error_file, wx.BITMAP_TYPE_ANY)
            self.error_tile = self.error_tile_image.ConvertToBitmap()
        else:
            self.error_tile_image = PyEmbeddedImage(self.ErrorImage)
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

    def GetInfo(self, level):
        """Get tile info for a particular level.

        level  the level to get tile info for

        Returns (num_tiles_x, num_tiles_y, ppd_x, ppd_y).

        Note that ppd_? may be meaningless for some tiles, so its
        value will be None.
        """

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
        else KeyError:
            # start process of getting tile from 'net, return 'pending' image
            self.GetInternetTile(self.level, x, y)
            tile = self.pending_tile

        return tile

    def GetInternetTile(self, level, x, y):
        """Start the process to get internet tile.

        level, x, y  identify the required tile

        If we aren't already getting this tile, queue a request and
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
        pass


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
