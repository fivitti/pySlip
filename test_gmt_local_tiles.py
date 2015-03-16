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
    def setUp(self):
        log.info('setUp')

    def tearDown(self):
        log.info('tearDown')

    def testSimple(self):
        """Simple tests."""

        log.info('testSimple')
        t = gmt_local_tiles.GMTTiles(tiles_dir=TilesDir)
        for level in [0, 1, 2, 3, 4, 5, 6]:
            bmp = None
            l = t.UseLevel(level)
            if l:
                bmp = t.GetTile(1, 1)
                print('level=%d, l=%s, b=%s' % (level, str(l), str(bmp)))


app = wx.App()
app_frame = AppFrame()
app_frame.Show()
app.MainLoop()
