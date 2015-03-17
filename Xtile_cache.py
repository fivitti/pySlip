#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
An in-memory and disk cache for pySlip tiles.

Requires a wxPython application to be created before use.
If we can create a wx bitmap without wxPython, we could remove this dependency.
"""

import os
import wx

# if we don't have log.py, don't crash
try:
    import log
    #log = log.Log('pyslip.log', log.Log.DEBUG)
    log = log.Log('pyslip.log', log.Log.INFO)
except ImportError:
    def log(*args, **kwargs):
        pass


######
# Class to cache pySlip tiles in memory with a disk backing store.
######

class TileCache(object):
    """An object that caches tiles in memory and on disk.
    
    Only a limited number of tiles for each level in memory, unlimited
    number of tiles in disk backing store.
    """

    # path to tile in on-disk cache, %params are (x, y)
    # tiles are stored in path X/Y.png where X and Y are tile coord integers
    TilePath = os.path.join('%d', '%d.png')

    # maximum number of in-memory tiles for each level
    DefaultMaxInMem = 4000

    def __init__(self, cache_dir, levels, max_in_mem=DefaultMaxInMem):
        """Create the tile cache.

        cache_dir  path to a possibly existing directory cache of tiles
        levels     list of level numbers that will be used
        """

        # prepare tile cache if not already there
        self.cache_dir = cache_dir
        if not os.path.isdir(cache_dir):
            if os.path.isfile(cache_dir):
                msg = ("%s doesn't appear to be a tile cache directory"
                       % cache_dir)
                raise Exception(msg)
            os.makedirs(cache_dir)
        for level in levels:
            level_dir = os.path.join(cache_dir, '%d' % level)
            if not os.path.isdir(level_dir):
                os.makedirs(level_dir)

        # setup the tile in-memory level caches and LRU lists, etc
        self.max_in_mem = max_in_mem
        self.mem_cache = {}
        self.lru = {}
        for l in levels:
            self.mem_cache[l] = {}
            self.lru[l] = []

    def GetTile(self, level, x, y):
        """Get bitmap for tile at level,x,y.

        level  level to get tile from
        x      X coord of tile required (tile coordinates)
        y      Y coord of tile required (tile coordinates)

        Return tile from the local cache, return None if not found.
        """

        log.info('GetTile: %d,%d,%d' % (level, x, y))

        # the tile 'key' - just X and Y tile coordinates as a tuple
        tile_key = (x, y)

        try:
            # if tile in cache, return it from there
            bitmap = self.mem_cache[level][tile_key]
            self.lru[level].remove((x, y))      # remove, add at recent end
            self.lru[level].insert(0, tile_key)
            log.info('GetTile: tile found in cache')
        except KeyError:
            log.info('GetTile: tile NOT in cache, look on disk')
            # tile *not* in memory cache look in disk cache
            tile_dir = os.path.join(self.cache_dir, '%d' % level)
            tile_path = os.path.join(tile_dir, self.TilePath % (x, y))
            if not os.path.exists(tile_path):
                log.info('GetTile: tile %s not found!' % tile_path)
                # tile not there, return None
                bitmap = None
            else:
                log.info('GetTile: found tile on disk')
                # we have the tile file - read into memory, cache & return
                image = wx.Image(tile_path, wx.BITMAP_TYPE_ANY)
                bitmap = image.ConvertToBitmap()
                self.mem_cache[level][tile_key] = bitmap
                self.lru[level].insert(0, tile_key)

                # newly cached tile, check if we must drop old cached tiles
                self._trim_cache(level)

        return bitmap

    def CacheTile(self, image, bitmap, level, x, y):
        """Save tile in the disk and in-memory cache.

        image   data to save in disk cache file
        bitmap  the tile bitmap to save in LRU cache
        level   level of the tile
        x       X coord of tile
        y       Y coord of tile
        """

        # the tile 'key'
        tile_key = (x, y)

        # put bitmap into the in-memory cache
        self.mem_cache[level][tile_key] = bitmap

        # add this tile at "most recent" end of the LRU list
        self.lru[level].insert(0, tile_key)

        # drop relatively unused tiles from in-memory cache
        self._trim_cache(level)

        # write data to the appropriate disk file
        tile_dir = os.path.join(self.cache_dir, '%d' % level)
        tile_path = os.path.join(tile_dir, self.TilePath % (x, y))
        dir_name = os.path.dirname(tile_path)
        try:
            os.makedirs(dir_name)
        except OSError:
            pass
        image.SaveFile(tile_path, wx.BITMAP_TYPE_JPEG)

    def _trim_cache(self, level):
        """Ensure the memory cache for a level isn't too large."""

        while len(self.lru[level]) > self.max_in_mem:
            tile_key = self.lru[level].pop()    # remove old tile from LRU
            try:
                del self.mem_cache[level][tile_key] # and remove from cache
            except KeyError:
                # don't worry about cache/lru mismatches
                pass

    def _get_cache_size(self, level):
        """Return the number of tiles in cache for 'level'"""

        return len(self.mem_cache[level])
