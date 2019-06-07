install: clean
	clear; python setup.py build; python setup.py install

release: clean
	clear; python setup.py sdist bdist_wheel
	twine upload dist/*

clean:
	rm -Rf build dist pySlipQt.egg-info/
