#
# To manage the pySlip project a little
#

run:
	python pyslip_demo.py -t gmt
	#python -Qwarnall pyslip_demo.py -t gmt
	#python -3 pyslip_demo.py -t gmt

test:
	python test_assumptions.py
	python test_gmt_local_tiles.py
	python test_osm_tiles.py

clean:
	rm -Rf *.pyc *.log *.jpg
	(cd pyslip; rm -Rf *.pyc *.log)
	(cd pyslip/examples; rm -Rf *.pyc *.log)
