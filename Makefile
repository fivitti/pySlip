#
# To manage the pySlip project a little
#

test:
	python test_gmt_local_tiles.py
	python test_osm_tiles.py


clean:
	rm -Rf *.pyc *.log *.jpg
