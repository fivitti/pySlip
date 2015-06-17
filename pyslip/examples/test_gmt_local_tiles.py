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
import pyslip.gmt_local_tiles as gmt_local_tiles

import unittest
import shutil
from wx.lib.embeddedimage import PyEmbeddedImage


# where the pre-generated GMT tiles are
TilesDir = './gmt_tiles'

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

        # read all tiles in all rows of all levels
        cache = gmt_local_tiles.GMTTiles(tiles_dir=TilesDir)
        for level in cache.levels:
            cache.UseLevel(level)
            info = cache.GetInfo(level)
            if info:
                width_px = self.TileWidth * cache.num_tiles_x
                height_px = self.TileHeight * cache.num_tiles_y
                ppd_x = cache.ppd_x
                ppd_y = cache.ppd_y
                num_tiles_width = int(width_px / self.TileWidth)
                num_tiles_height = int(height_px / self.TileHeight)
                for x in range(num_tiles_width):
                    for y in range(num_tiles_height):
                        bmp = cache.GetTile(x, y)
                        msg = "Can't find tile (%d,%d,%d)!?" % (level, x, y)
                        self.failIf(bmp is None, msg)

    def testErrors(self):
        """Test possible errors."""

        # try to use on-disk cache that doesn't exist
        with self.assertRaises(IOError):
            cache = gmt_local_tiles.GMTTiles(tiles_dir='_=XYZZY=_')

        # check that using level outside map levels returns None
        cache = gmt_local_tiles.GMTTiles(tiles_dir=TilesDir)
        level = cache.levels[-1] + 1      # get level # that DOESN'T exist
        msg = "Using bad level (%d) didn't raise exception?" % level
        with self.assertRaises(Exception, msg=msg):
            cache.UseLevel(level)

        # check that reading tile outside map returns None
        cache = gmt_local_tiles.GMTTiles(tiles_dir=TilesDir)
        level = cache.levels[0] # known good level
        cache.UseLevel(level)
        width_px = self.TileWidth * cache.num_tiles_x
        height_px = self.TileHeight * cache.num_tiles_y
        ppd_x = cache.ppd_x
        ppd_y = cache.ppd_y
        num_tiles_width = int(width_px / self.TileWidth)
        num_tiles_height = int(height_px / self.TileHeight)
        bmp = cache.GetTile(num_tiles_width, num_tiles_height)
        self.assertTrue(bmp is None,
                        'Using bad coords (%d,%d) got bmp=%s'
                        % (num_tiles_width, num_tiles_height, str(bmp)))

    def XtestConvert(self):
        """Test geo2map conversions.

        This is normally turned off as it is a "by hand" sort of check.
        """

        cache = gmt_local_tiles.GMTTiles(tiles_dir=TilesDir)

        # get tile covering Greenwich observatory
#        xgeo = -0.0005  # Greenwich observatory
#        ygeo = 51.4768534
        xgeo = 7.605916 # Deutsches Eck
        ygeo = 50.364444
        for level in [0, 1, 2, 3, 4]:
            cache.UseLevel(level)
            (xtile, ytile) = cache.Geo2Tile(xgeo, ygeo)
            bmp = cache.GetTile(int(xtile), int(ytile))

            pt_px_x = int((xtile - int(xtile)) * cache.tile_size_x)
            pt_px_y = int((ytile - int(ytile)) * cache.tile_size_y)

            dc = wx.MemoryDC()
            dc.SelectObject(bmp)
            text = "o"
            (tw, th) = dc.GetTextExtent(text)
            dc.DrawText(text, pt_px_x-tw/2,  pt_px_y-th/2)
            dc.SelectObject(wx.NullBitmap)

            bmp.SaveFile('xyzzy_%d.jpg' % level, wx.BITMAP_TYPE_JPEG)

app = wx.App()
app_frame = AppFrame()
app_frame.Show()
app.MainLoop()
