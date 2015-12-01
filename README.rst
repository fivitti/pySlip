pySlip
======

pySlip is a 'slip map' widget for wxPython.

**This is the GitHub version of the Google Code pySlip project at
https://code.google.com/p/pyslip.
The 2.X versions of code will remain on Google.
The 3.X versions will be developed here on GitHub.**

During my work writing geophysical applications in python I often wanted to
display a map that was very large - many hundreds of thousands of pixels in
width.  I searched around for a GUI solution that would work rather like Google
maps: tiled, layers, etc.  I couldn't find anything that didn't assume
browser+map server.  So I wrote my own wxPython widget.  This worked well for
cartesian self-generated maps and has been extended to handle non-cartesian
maps and tiles sourced from places like OpenStreetMap.

It's a poor thing, but solves my problem.  I'm placing it here in the hope that
someone else may find it useful.  If you find it useful, or make improvements
to it, drop me a line.

pySlip works on Linux, Mac and Windows.  It only works with wxPython 2.x and
Python 2.x (at the moment).  At some point when wxPython matures I hope to
move to Python 3.X and later versions of wxPython.

