install: clean
	clear; python setup.py build; python setup.py install

release: #clean
	@echo "**********************************************"
	@echo "* read ~/installs/pypi.txt before doing this *"
	@echo "**********************************************"
	@read ignore
	@status="$(git status | grep \"modified:\")"
	echo $(status)
	@test -n "$(status)"; echo 'There are modified files.'; exit 1
	@status="$(git status | grep \"branch is ahead of\")"
	echo $(status)
	@test -n "$(status)"; echo 'There are uncommitted files.'; exit 2
#	$(eval RELNUM := $(shell ./bump_release))
#	cp PyPi_README.rst README.rst
#	python3 setup.py sdist bdist_wheel
#	git tag $(RELNUM) -m "$(RELNUM) release"
#	git push --tags origin master
#	rm -Rf build dist pyslip.egg-info
#	python3 setup.py sdist bdist_wheel
#	-twine upload dist/*
#	cp github_README.rst README.rst

clean:
	rm -Rf build dist pySlipQt.egg-info/
