#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test the local GMT tiles code.

Requires a wxPython application to be created before use.
If we can create a bitmap without wxPython, we could remove this dependency.
"""

import os
import glob
import pickle
import wx
import gmt_local_tiles

import log
import unittest
import shutil
from wx.lib.embeddedimage import PyEmbeddedImage


# if we don't have log.py, don't crash
try:
    import log
    log = log.Log('pyslip.log', log.Log.DEBUG)
except ImportError:
    def log(*args, **kwargs):
        pass


TilesDir = '/Users/r-w/pyslip/tiles'

DefaultAppSize = (512, 512)
DemoName = 'GMT Tiles Cache Test'
DemoVersion = '0.1'


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
        self.Destroy()

class TestGMTTiles(unittest.TestCase):

    # for GMT tiles
    TileWidth = 256
    TileHeight = 256

    def testSimple(self):
        """Simple tests."""

        log.info('testSimple')

        # read all tiles in all rows of all levels
        cache = gmt_local_tiles.GMTTiles(tiles_dir=TilesDir)
        for level in cache.levels:
            info = cache.UseLevel(level)
            if info:
                (width_px, height_px, ppd_x, ppd_y) = info
                num_tiles_width = int(width_px / self.TileWidth)
                num_tiles_height = int(height_px / self.TileHeight)
                for x in range(num_tiles_width):
                    for y in range(num_tiles_height):
                        bmp = cache.GetTile(x, y)
                        msg = "Can't find tile (%d,%d,%d)!?" % (level, x, y)
                        self.failIf(bmp is None, msg)
            else:
                print('level %d not available' % level)

    def testErrors(self):
        """Test possible errors."""

        log.info('testErrors')

        # try to use on-disk cache that doesn't exist
        with self.assertRaises(IOError):
            cache = gmt_local_tiles.GMTTiles(tiles_dir='_=XYZZY=_')

        # check that using level outside map levels returns None
        cache = gmt_local_tiles.GMTTiles(tiles_dir=TilesDir)
        level = cache.levels[-1] + 1      # get level # that DOESN'T exist
        info = cache.UseLevel(level)
        self.assertTrue(info is None,
                        'Using bad level (%d) got info=%s' % (level, str(info)))

        # check that reading tile outside map returns None
        cache = gmt_local_tiles.GMTTiles(tiles_dir=TilesDir)
        level = cache.levels[0]
        info = cache.UseLevel(level)
        (width_px, height_px, ppd_x, ppd_y) = info
        num_tiles_width = int(width_px / self.TileWidth)
        num_tiles_height = int(height_px / self.TileHeight)
        self.assertFalse(info is None,
                        'Using good level (%d) got info=%s' % (level, str(info)))
        bmp = cache.GetTile(num_tiles_width, num_tiles_height)
        self.assertTrue(bmp is None,
                        'Using bad coords (%d,%d) got bmp=%s'
                        % (num_tiles_width, num_tiles_height, str(bmp)))


app = wx.App()
app_frame = AppFrame()
app_frame.Show()
app.MainLoop()
