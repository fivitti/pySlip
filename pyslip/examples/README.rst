Programs in this directory
==========================

The programs here all assume that pySlip has been installed.  They are used to
test pySlip and to demonstrate some of the capabilities of the widget:

=======================  =======
Program                  Details
=======================  =======
pyslip_demo.py           demonstrates some capabilities of pySlip
appstaticbox.py              part of pyslip_demo.py
display_text.py              part of pyslip_demo.py
layer_control.py             part of pyslip_demo.py
rotextctrl.py                part of pyslip_demo.py
test_image_placement.py  allows playing with image placement
test_point_placement.py  allows playing with point placement
test_poly_placement.py   allows playing with polygon placement
test_text_placement.py   allows playing with text placement
test_gotoposition.py     test the "goto position" code
test_assumptions.py      test some assumptions made in pySlip
test_gmt_local_tiles.py  simplistic test of GMT tiles
test_osm_tiles.py        simplistic test of OSM tiles
test_maprel_image.py     simple test of map-relative image placement
test_maprel_poly.py      simple test of map-relative polygon placement
test_maprel_text.py      simple test of map-relative text placement
test_multi_widget.py     simple multi-widget test - look for interaction
test_viewrel_image.py    simple test of view-relative image placement
test_viewrel_point.py    simple test of view-relative point placement
test_viewrel_poly.py     simple test of view-relative polygon placement
test_viewrel_text.py     simple test of view-relative text placement
=======================  =======

Other things here:

=======================  =======
Directory                What it is
=======================  =======
gmt_tiles.tar.gz         pre-generated GMT tiles (tar format)
gmt_local_tiles.zip      pre-generated GMT tiles (zip format)
graphics                 graphics files used by the programs here
=======================  =======

GMT tiles
---------

Before running *pyslip_demo.py* you must copy one of the compressed GMT local
tiles files to your home directory and unpack it there.  That should rsult in 
a directory named *gmt_local_tiles*.


Note
----

The test *test_assumptions.py* fails due to some code in pySlip not being as
fast as it might be.  Some of the ideas tested in *test_assumptions.py* might
be put into pySlip, but some may not.
