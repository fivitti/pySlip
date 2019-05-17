#!/usr/bin/env python

"""
A _base_ Tiles object for pySlip tiles.

All tile sources should inherit from this base class.
For example, see gmt_local_tiles.py and osm_tiles.py.

A local tileset is instantiated by specifying 'tiles_dir', nothing else
is required.

An internet tileset requires 'servers' and 'callback', nothing else
is required.
"""

import os
import os.path
import time
import math
import threading
import traceback
import urllib.request
import queue
import wx

from . import pycacheback
from . import sys_tile_data as std
from . import logger
logger = logger.Logger('pyslip.log')


# set how old disk-cache tiles can be before we re-request them from the internet
# this is the number of days old a tile is before we re-request
# if 'None', never re-request tiles after first satisfied request
RefreshTilesAfterDays = 60


################################################################################
# Worker class for internet tile retrieval
################################################################################

class TileWorker(threading.Thread):
    """Thread class that gets request from queue, loads tile, calls callback."""

    def __init__(self, id, server, tilepath, requests, callback,
                 error_tile, content_type, filetype, rerequest_age):
        """Prepare the tile worker.

        id            a unique nuer identifying the worker instance
        server        server URL
        tilepath      path to tile on server
        requests      the request queue
        callback      function to call after tile available
        content_type  expected Content-Type string
        filetype      wxPython integer filetype

        Results are returned in the callback() params.
        """

        threading.Thread.__init__(self)

        self.id = id
        self.server = server
        self.tilepath = tilepath
        self.requests = requests
        self.callback = callback
        self.error_tile_image = error_tile
        self.content_type = content_type
        self.filetype = filetype
        self.daemon = True

    def run(self):
        while True:
            # get zoom level and tile coordinates to retrieve
            (level, x, y) = self.requests.get()

            image = self.error_tile_image
            error = False       # True if we get an error
            try:
                tile_url = self.server + self.tilepath.format(Z=level, X=x, Y=y)
                f = urllib.request.urlopen(urllib.request.Request(tile_url))
                content_type = f.info().getheader('Content-Type')
                if content_type == self.content_type:
                    image = wx.ImageFromStream(f, self.filetype)
                else:
                    error = True
            except Exception as e:
                error = True
                logger('%s exception getting tile %d,%d,%d from %s\n%s'
                       % (type(e).__name__, level, x, y, tile_url, e.message))

            # call the callback function passing level, x, y and image data
            # error is False if we want to cache this tile on-disk
            wx.CallAfter(self.callback, level, x, y, image, error)

            # finally, removes request from queue
            self.requests.task_done()

################################################################################
# Define a cache for tiles
################################################################################

class Cache(pycacheback.pyCacheBack):
    """Cache for local or internet tiles.

    Instance variables we use from pyCacheBack:
        self._tiles_dir  path to the on-disk cache directory
    """

    # always save tiles to disk with this format
    TileDiskFormat = wx.BITMAP_TYPE_PNG

    # tiles stored on disk at <self.tiles_dir>/<TilePath>
    TilePath = '{Z}/{X}/{Y}.tile'

    def tile_date(self, key):
        """Return the creation date of a tile given its key."""

        tile_path = self.tile_path(key)
        return os.path.getctime(tile_path)

    def tile_path(self, key):
        """Return path to a tile file given its key."""

        (level, x, y) = key
        file_path = os.path.join(self._tiles_dir,
                                 self.TilePath.format(Z=level, X=x, Y=y))
        return file_path

    def _get_from_back(self, key):
        """Retrieve value for 'key' from backing storage.

        key  tuple (level, x, y)
             where level is the level of the tile
                   x, y  is the tile coordinates (integer)

        Raises KeyError if tile not found.
        """

        # look for item in disk cache
        file_path = self.tile_path(key)
        if not os.path.exists(file_path):
            # tile not there, raise KeyError
            raise KeyError("Item with key '%s' not found in on-disk cache"
                           % str(key))

        # we have the tile file - read into memory & return
        return wx.Image(file_path, self.TileDiskFormat).ConvertToBitmap()

    def _put_to_back(self, key, image):
        """Put a image into on-disk cache.

        image   the wx.Image to save
        key     a tuple: (level, x, y)
                where level  level for image
                      x      integer tile coordinate
                      y      integer tile coordinate
        """

        (level, x, y) = key
        tile_path = os.path.join(self._tiles_dir,
                                 self.TilePath.format(Z=level, X=x, Y=y))
        dir_path = os.path.dirname(tile_path)
        try:
            os.makedirs(dir_path)
        except OSError:
            # we assume it's a "directory exists' error, which we ignore
            pass

        image.SaveFile(tile_path, self.TileDiskFormat)

###############################################################################
# Base class for a tile source - handles access to a source of tiles.
###############################################################################

class BaseTiles(object):
    """A base tile object to source tiles for pySlip.

    Source either local tiles or internet tiles.
    """

    # maximum number of outstanding requests per server
    MaxServerRequests = 2

    # maximum number of in-memory cached tiles
    MaxLRU = 1000

    # allowed file types and associated values
    AllowedFileTypes = {'jpg': wx.BITMAP_TYPE_JPEG,
                        'png': wx.BITMAP_TYPE_PNG,
                       }

    # the number of seconds in a day
    SecondsInADay = 60 * 60 * 24

    def __init__(self, levels, tile_width, tile_height, servers=None,
                 url_path=None, max_server_requests=MaxServerRequests,
                 callback=None, max_lru=MaxLRU, tiles_dir=None,
                 http_proxy=None, refetch_days=None):
        """Initialise a Tiles instance.

        levels               a list of level numbers that are to be served
        tile_width           width of each tile in pixels
        tile_height          height of each tile in pixels
        servers              list of internet tile servers (None if local tiles)
        url_path             path on server to each tile (ignored if local tiles)
        max_server_requests  maximum number of requests per server (ignored if local tiles)
        callback             method to call when internet tile recieved (ignored if local tiles)
        max_lru              maximum number of cached in-memory tiles
        tiles_dir            path to on-disk tile cache directory
        http_proxy           proxy to use if required
        """

        # save params
        self.levels = levels
        self.tile_size_x = tile_width
        self.tile_size_y = tile_height
        self.servers = servers
        self.url_path = url_path
        self.max_lru = max_lru
        self.tiles_dir = tiles_dir
        self.available_callback = callback
        self.max_requests = max_server_requests

        # calculate a re-request age, if specified
        self.rerequest_age = 0
        if RefreshTilesAfterDays is not None:
            self.rerequest_age = (time.time() -
                                      RefreshTilesAfterDays * self.SecondsInADay)
        if refetch_days is not None:
            self.rerequest_age = (time.time() - refetch_days * self.SecondsInADay)

        # set min and max tile levels and current level
        self.min_level = min(self.levels)
        self.max_level = max(self.levels)
        self.level = self.min_level

        # setup the tile cache (note, no callback set since net unused)
        self.cache = Cache(tiles_dir=tiles_dir, max_lru=max_lru)

        #####
        # Now finish setting up
        #####

        # tiles extent for tile data (left, right, top, bottom)
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

        # if we are serving local tiles, just return
        if self.servers is None:
            return

        #####
        # otherwise prepare for internet work
        #####

        # figure out tile filename extension from 'url_path'
        tile_extension = os.path.splitext(url_path)[1][1:]
        tile_extension_lower = tile_extension.lower()      # ensure lower case

        # determine the file bitmap type
        try:
            self.filetype = self.AllowedFileTypes[tile_extension_lower]
        except KeyError as e:
            raise TypeError("Bad tile_extension value, got '%s', "
                            "expected one of %s"
                            % (str(tile_extension),
                               str(self.AllowedFileTypes.keys())))

        # compose the expected 'Content-Type' string on request result
        # if we get here we know the extension is in self.AllowedFileTypes
        if tile_extension_lower == 'jpg':
            self.content_type = 'image/jpeg'
        elif tile_extension_lower == 'png':
            self.content_type = 'image/png'

        # set the list of queued unsatisfied requests to 'empty'
        self.queued_requests = {}

        # prepare the "pending" and "error" images
        self.pending_tile_image = std.getPendingImage()
        self.pending_tile = self.pending_tile_image.ConvertToBitmap()

        self.error_tile_image = std.getErrorImage()
        self.error_tile = self.error_tile_image.ConvertToBitmap()

        # test for firewall - use proxy (if supplied)
        test_url = self.servers[0] + self.url_path.format(Z=0, X=0, Y=0)
        try:
            urllib.request.urlopen(test_url)
        except Exception as e:
            logger('%s exception doing simple connection to: %s'
                   % (type(e).__name__, test_url))
            logger(''.join(traceback.format_exc()))

            if http_proxy:
                proxy = urllib.request.ProxyHandler({'http': http_proxy})
                opener = urllib.request.build_opener(proxy)
                urllib.request.install_opener(opener)
                try:
                    urllib.request.urlopen(test_url)
                except:
                    msg = ("Using HTTP proxy %s, "
                           "but still can't get through a firewall!")
                    raise Exception(msg)
            else:
                msg = ("There is a firewall but you didn't "
                       "give me an HTTP proxy to get through it?")
                raise Exception(msg)

        # set up the request queue and worker threads
        self.request_queue = queue.Queue()  # entries are (level, x, y)
        self.workers = []
        for server in self.servers:
            for num_threads in range(self.max_requests):
                worker = TileWorker(num_threads, server, self.url_path,
                                    self.request_queue, self._tile_available,
                                    self.error_tile_image, self.content_type,
                                    self.filetype, self.rerequest_age)
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

        Return True if level change occurred, else False if not possible.
        """

        # first, CAN we zoom to this level?
        if level not in self.levels:
            return False

        # get tile info
        info = self.GetInfo(level)
        if info is None:
            return False

        # OK, save new level
        self.level = level
        (self.num_tiles_x, self.num_tiles_y, self.ppd_x, self.ppd_y) = info

        # flush any outstanding requests.
        # we do this to speed up multiple-level zooms so the user doesn't
        # sit waiting for tiles to arrive that won't be shown.
        self.FlushRequests()

        return True

    def GetTile(self, x, y):
        """Get bitmap for tile at tile coords (x, y) and current level.

        x  X coord of tile required (tile coordinates)
        y  Y coord of tile required (tile coordinates)

        Returns bitmap object for the tile image.
        Tile coordinates are measured from map top-left.

        We override the existing GetTile() method to add code to retrieve
        tiles from the internet if not in on-disk cache.

        We also check the date on the tile from disk-cache.  If "too old",
        return it after starting the process to get new tile from internet.
        """

        try:
            # get tile from cache
            tile = self.cache[(self.level, x, y)]
        except KeyError as e:
            # if we are serving local tiles, this is an error
            if self.servers is None:
                raise KeyError("Can't find tile for key '%s'"
                               % str((self.level, x, y)))

            # otherwise, start process of getting tile from 'net, return 'pending' image
            self._get_internet_tile(self.level, x, y)
            tile = self.pending_tile
        else:
            # get tile from cache, if using internet check date
            if self.servers is not None:
                tile_date = self.cache.tile_date((self.level, x, y))
                if tile_date < self.rerequest_age:
                    self._get_internet_tile(self.level, x, y)

        return tile

    def GetInfo(self, level):
        """Get tile info for a particular level.

        level  the level to get tile info for

        Returns (num_tiles_x, num_tiles_y, ppd_x, ppd_y) or None if 'level'
        doesn't exist.

        Note that ppd_? may be meaningless for some tiles, so its
        value will be None.

        This method is for internet tiles.  It will be overridden for GMT tiles.
        """

        # is required level available?
        if level not in self.levels:
            return None

        # otherwise get the information
        self.num_tiles_x = int(math.pow(2, level))
        self.num_tiles_y = int(math.pow(2, level))

        return (self.num_tiles_x, self.num_tiles_y, None, None)

    def FlushRequests(self):
        """Delete any outstanding tile requests."""

        # if we are serving internet tiles ...
        if self.servers:
            self.request_queue.queue.clear()
            self.queued_requests.clear()

    def _get_internet_tile(self, level, x, y):
        """Start the process to get internet tile.

        level, x, y  identify the required tile

        If we don't already have this tile (or getting it), queue a request and
        also put the request into a 'queued request' dictionary.  We
        do this since we can't peek into a queue to see what's there.
        """

        tile_key = (level, x, y)
        if tile_key not in self.queued_requests:
            # add tile request to the server request queue
            self.request_queue.put(tile_key)
            self.queued_requests[tile_key] = True

    def _tile_available(self, level, x, y, image, error):
        """A tile is available.

        level   level for the tile
        x       x coordinate of tile
        y       y coordinate of tile
        image   tile image data
        error   True if image is 'error' image
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

    def SetAgeThresholdDays(self, num_days):
        """Set the tile refetch threshold time.

        num_days  number of days before refetching tiles

        If 'num_days' is 0 refetching is inhibited.
        """

        global RefreshTilesAfterDays

        # update the global in case we instantiate again
        RefreshTilesAfterDays = num_days

        # recalculate this instance's age threshold in UNIX time
        self.rerequest_age = (time.time() -
                                  RefreshTilesAfterDays * self.SecondsInADay)

    def Geo2Tile(self, xgeo, ygeo):
        """Convert geo to tile fractional coordinates for level in use.

        xgeo   geo longitude in degrees
        ygeo   geo latitude in degrees

        Note that we assume the point *is* on the map!
        """

        raise Exception('You must override Tiles.Geo2Tile()')

    def Tile2Geo(self, xtile, ytile):
        """Convert tile fractional coordinates to geo for level in use.

        xtile  tile fractional X coordinate
        ytile  tile fractional Y coordinate

        Note that we assume the point *is* on the map!
        """

        raise Exception('You must override Tiles.Tile2Geo()')
