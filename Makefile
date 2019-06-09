install: clean
	clear; python setup.py build; python setup.py install

# read ~/installs/pypi.txt before doing this
release: clean
	echo "**********************************************"
	echo "* read ~/installs/pypi.txt before doing this *"
	echo "**********************************************"
	read ignore
	mv README.rst github_README.rst
	mv PyPi_README.rst README.rst
	clear; python setup.py sdist bdist_wheel
	twine upload dist/*
	mv README.rst PyPi_README.rst
	mv github_README.rst README.rst

clean:
	rm -Rf build dist pySlipQt.egg-info/
