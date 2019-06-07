pySlip
======

pySlip is a 'slip map' widget for wxPython.

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

The earlier 3.0.x release was for python 2.x only on Windows, Linux and macOS.
This version works with wxPython 4.0+ and Python 3.6+.  It may work on earlier
python 3 versions, but this has not been tested.  It has been tested on Linux
but not Windows or macOS, yet.

The widget API is documented in
`the wiki <https://github.com/rzzzwilson/pySlip/wiki/The-pySlip-API>`_.
