#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test the OSM tiles code.

Requires a wxPython application to be created before use.
If we can create a bitmap without wxPython, we could remove this dependency.
"""

import os
import glob
import pickle
import wx
import osm_tiles

import unittest
import shutil
from wx.lib.embeddedimage import PyEmbeddedImage


# where the OSM tiles are cached on disk
TilesDir = '/Users/r-w/pyslip/tiles'

DefaultAppSize = (512, 512)
DemoName = 'OSM Tiles Cache Test'
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

class TestOSMTiles(unittest.TestCase):

    # for OSM tiles
    TileWidth = 256
    TileHeight = 256

    def testSimple(self):
        """Simple tests."""

        # read all tiles in all rows of all levels
        cache = osm_tiles.OSMTiles(tiles_dir=TilesDir)
        for level in cache.levels:
            info = cache.UseLevel(level)
            if info:
                (width_px, height_px, ppd_x, ppd_y) = info
                num_tiles_width = int(width_px / self.TileWidth)
                num_tiles_height = int(height_px / self.TileHeight)
#                for x in range(num_tiles_width):
#                    for y in range(num_tiles_height):
                for x in range(4):
                    for y in range(4):
                        bmp = cache.GetTile(x, y)
                        msg = "Can't find tile (%d,%d,%d)!?" % (level, x, y)
                        self.failIf(bmp is None, msg)
            else:
                print('level %d not available' % level)

    def testErrors(self):
        """Test possible errors."""

        # check that using level outside map levels returns None
        cache = osm_tiles.OSMTiles(tiles_dir=TilesDir)
        level = cache.levels[-1] + 1      # get level # that DOESN'T exist
        info = cache.UseLevel(level)
        self.assertTrue(info is None,
                        'Using bad level (%d) got info=%s' % (level, str(info)))

        # check that reading tile outside map returns None
        cache = osm_tiles.OSMTiles(tiles_dir=TilesDir)
        level = cache.levels[0]
        info = cache.UseLevel(level)
        (width_px, height_px, ppd_x, ppd_y) = info
        num_tiles_width = int(width_px / self.TileWidth)
        num_tiles_height = int(height_px / self.TileHeight)
        self.assertFalse(info is None,
                        'Using good level (%d) got info=%s' % (level, str(info)))
# OSM returns an empty tile if you request outside map limits
#        bmp = cache.GetTile(num_tiles_width, num_tiles_height)
#        self.assertTrue(bmp is None,
#                        'Using bad coords (%d,%d) got bmp=%s'
#                        % (num_tiles_width, num_tiles_height, str(bmp)))
        info = cache.UseLevel(1)
        bmp = cache.GetTile(0, 0)
        bmp.SaveFile('xyzzy00.jpg', wx.BITMAP_TYPE_JPEG)
        bmp = cache.GetTile(0, 1)
        bmp.SaveFile('xyzzy01.jpg', wx.BITMAP_TYPE_JPEG)
        bmp = cache.GetTile(1, 0)
        bmp.SaveFile('xyzzy10.jpg', wx.BITMAP_TYPE_JPEG)
        bmp = cache.GetTile(1, 1)
        bmp.SaveFile('xyzzy11.jpg', wx.BITMAP_TYPE_JPEG)


app = wx.App()
app_frame = AppFrame()
app_frame.Show()
app.MainLoop()
