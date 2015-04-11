#
# To manage the pySlip project a little
#

run:
	python pyslip_demo.py -t gmt

test:
	python test_assumptions.py
	python test_gmt_local_tiles.py
	python test_osm_tiles.py

clean:
	rm -Rf *.pyc *.log *.jpg
